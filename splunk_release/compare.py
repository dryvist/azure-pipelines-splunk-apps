"""Compare exported and packaged apps and write deployment reports."""

import difflib
import filecmp
import html
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from splunk_release.azure import print_colored_patch, run
from splunk_release.package import sort_confs

def archives(directory):
    """Map app id to archive: <app-id>.tgz (export) or <app-id>-<version>.tar.gz (package)."""
    found = {}
    for archive in Path(directory).glob("*gz"):
        name = archive.name
        app = name.removesuffix(".tgz") if name.endswith(".tgz") else name.rsplit("-", 1)[0]
        found[app] = archive
    return found

def extract(archive, dest):
    """Extract archive into dest without its top folder; an empty dest when archive is None."""
    raw = dest.with_name(dest.name + "-raw")
    raw.mkdir()
    if archive:
        with tarfile.open(archive) as tar:
            tar.extractall(raw, filter="data")
    entries = list(raw.iterdir())
    (entries[0] if len(entries) == 1 and entries[0].is_dir() else raw).rename(dest)

def files(root):
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}

def kept(path):
    """Files a deploy does not replace: local/, metadata/local.meta and users/."""
    return path.parts[0] in ("local", "users") or path.parts[:2] == ("metadata", "local.meta")

def merge_local(root):
    """Promote local configuration into default files and copy other local files."""
    local = root / "local"
    if local.exists():
        for relative in sorted(files(local)):
            source = local / relative
            target = root / "default" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix == ".conf":
                subprocess.run(
                    ["ksconf", "promote", "--batch", str(source), str(target)],
                    check=True,
                )
            else:
                shutil.copy2(source, target)
    local_meta = root / "metadata" / "local.meta"
    if local_meta.exists():
        default_meta = root / "metadata" / "default.meta"
        default_meta.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ksconf", "promote", "--batch", str(local_meta), str(default_meta)],
            check=True,
        )
    sort_confs(root / "default")

def deployed(path):
    """Files a deploy compares: default/ and metadata/default.meta."""
    return path.parts[0] == "default" or path == Path("metadata/default.meta")

def merged_archive(app, root, path):
    """Write an app archive without local/, users/ or metadata/local.meta."""
    def keep(info):
        relative = Path(info.name).relative_to(app)
        return None if relative.parts and kept(relative) else info

    with tarfile.open(path, "w:gz") as archive:
        archive.add(root, arcname=app, filter=keep)

def listed(paths):
    return [f"- {p.as_posix()}" for p in sorted(paths)] or ["- None"]

def deployed_changes(target, source):
    t, s = files(target), files(source)
    changes = []
    for p in sorted(p for p in t | s if deployed(p)):
        if p not in t:
            status = "Added"
        elif p not in s:
            status = "Removed"
        elif not filecmp.cmp(target / p, source / p, shallow=False):
            status = "Changed"
        else:
            continue
        changes.append((status, p))
    return changes

def change_tree(changes):
    lines, folders = [], set()
    for status, path in changes:
        for depth in range(1, len(path.parts)):
            folder = path.parts[:depth]
            if folder not in folders:
                lines.append("  " * (depth - 1) + f"{path.parts[depth - 1]}/")
                folders.add(folder)
        lines.append("  " * (len(path.parts) - 1) + f"{path.name} [{status.lower()}]")
    return "\n".join(lines) or "No deployed file changes."

def summary(target, source, target_before, source_before):
    changes = deployed_changes(target, source)
    deployed = [f"- {status}: {path.as_posix()}" for status, path in changes]
    return "\n".join([
        "## Deployed change tree",
        "```text",
        change_tree(changes),
        "```",
        "## Deployed changes", *(deployed or ["- None"]),
        "## Target local files (kept, not backed up)",
        "These files stay on the target after a deploy, override the deployed defaults, and are not backed up.",
        *listed(p for p in target_before if p.parts[0] != "users" and kept(p)),
        "## Source local files (not deployed)",
        "These files exist only in the source environment and are not part of the deploy.",
        *listed(p for p in source_before if p.parts[0] != "users" and kept(p)),
        "## User files",
        "Target:", *listed(p for p in target_before if p.parts[0] == "users"),
        "Source:", *listed(p for p in source_before if p.parts[0] == "users"),
    ]) + "\n"

def write_html_diff(app, target, source, changes, local_text, out):
    local = html.escape(local_text or "No local configuration files.\n")
    tables = "".join(
        f"<section><h2>{html.escape(path.as_posix())} ({status})</h2>"
        + difflib.HtmlDiff().make_table(
            (target / path).read_bytes().decode("utf-8", "replace").splitlines(True)
            if (target / path).exists() else [],
            (source / path).read_bytes().decode("utf-8", "replace").splitlines(True)
            if (source / path).exists() else [],
            fromdesc=html.escape(f"target/{path.as_posix()}"),
            todesc=html.escape(f"source/{path.as_posix()}"),
            context=True,
            numlines=3,
        ) + "</section>"
        for status, path in changes
    )
    page = f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(app)} diff</title>'
    page += "<style>body{font-family:Arial;margin:2em}table.diff{border-collapse:collapse;width:100%}"
    page += "td,th{padding:.2em;vertical-align:top}.diff_add{background:#cfc}"
    page += ".diff_sub{background:#fcc}.diff_chg{background:#ffc}</style></head><body>"
    page += f"<h1>{html.escape(app)} deployed diff</h1><pre>{html.escape(change_tree(changes))}</pre>"
    page += tables or "<p>No deployed file changes.</p>"
    page += f"<h2>Local vs default</h2><pre>{local}</pre></body></html>\n"
    (out / f"{app}-diff.html").write_text(page, encoding="utf-8")

def local_vs_default(target, source, work):
    """Compare each target local file with the same stanzas in the source default file, using ksconf."""
    pairs = [(c, source / "default" / c.relative_to(target / "local"))
             for c in sorted((target / "local").rglob("*.conf"))]
    if (target / "metadata" / "local.meta").exists():
        pairs.append((target / "metadata" / "local.meta", source / "metadata" / "default.meta"))
    report = []
    for number, (local, default) in enumerate(pairs):
        stanzas, subset = work / f"{number}.txt", work / f"{number}.conf"
        run(["ksconf", "filter", str(local), "--brief", "-o", str(stanzas)], check=True)
        if default.exists():
            run(["ksconf", "filter", str(default), "--match", "string", "--stanza", f"file://{stanzas}",
                 "-o", str(subset)], check=True)
        else:
            subset.write_text("")
        # ksconf diff exits 3 when the files differ.
        result = run(["ksconf", "diff", str(subset), str(local)], capture_output=True, text=True)
        name = local.relative_to(target).as_posix()
        report.append(f"=== {name} vs the same stanzas in the deployed default ===\n{result.stdout}\n")
    return "".join(report)

def diff(target_dir, source_dir, out_dir):
    """Write each app's merged archive, readable diffs, and Markdown summary."""
    targets, sources = archives(target_dir), archives(source_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for app in sorted(targets.keys() | sources.keys()):
        with tempfile.TemporaryDirectory() as tmp:
            target, source = Path(tmp, "target"), Path(tmp, "source")
            extract(targets.get(app), target)
            extract(sources.get(app), source)
            target_before, source_before = files(target), files(source)
            work = Path(tmp, "local-vs-default")
            work.mkdir()
            local_text = local_vs_default(target, source, work)
            (out / f"{app}-local-vs-default.diff").write_text(local_text, encoding="utf-8")
            print(f"##[section]{app}: target local files vs the deployed default")
            print(local_text or "No local configuration files.\n", end="")
            merge_local(target)
            merge_local(source)
            changes = deployed_changes(target, source)
            text = summary(target, source, target_before, source_before)
            write_html_diff(app, target, source, changes, local_text, out)
            merged_archive(app, target if app in targets else source, out / f"{app}-merged.tar.gz")
            for root in (target, source):
                for p in files(root):
                    if not deployed(p):
                        (root / p).unlink()
            patch = []
            for path in sorted(p for p in files(target) | files(source) if deployed(p)):
                old, new = (r / path for r in (target, source))
                patch.extend(difflib.diff_bytes(
                    difflib.unified_diff,
                    old.read_bytes().splitlines(keepends=True) if old.exists() else [],
                    new.read_bytes().splitlines(keepends=True) if new.exists() else [],
                    f"target/{path.as_posix()}".encode(), f"source/{path.as_posix()}".encode(),
                ))
        patch_text = b"".join(patch)
        (out / f"{app}.patch").write_bytes(patch_text)
        (out / f"{app}-summary.md").write_text(text, encoding="utf-8")
        print_colored_patch(patch_text)
        print(f"##vso[task.uploadsummary]{(out / f'{app}-summary.md').resolve()}")
        print(text, end="")

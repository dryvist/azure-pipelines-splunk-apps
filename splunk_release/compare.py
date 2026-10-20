"""Compare exported and packaged apps and write deployment reports."""

import difflib
import filecmp
import html
import re
import shutil
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

from splunk_release.azure import log, print_colored_patch, run
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
    drop_install_checksum(dest)

def drop_install_checksum(root):
    """Print, then remove, the install checksums Splunk Cloud writes to metadata/local.meta and app.conf."""
    drop_lines(root, root / "metadata" / "local.meta",
               r"^\[app/install/install_source_checksum\]\n(?:(?!\[).*\n?)*")
    for conf in sorted(root.rglob("app.conf")):
        drop_lines(root, conf, r"^install_source(?:_local)?_checksum\s*=.*\n?")

def drop_lines(root, path, pattern):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    found = re.findall(pattern, text, re.M)
    if not found:
        return
    log("section", f"{root.name} {path.relative_to(root).as_posix()} install checksum (not compared)")
    print("".join(found).strip())
    rest = re.sub(pattern, "", text, flags=re.M)
    if re.search(r"^[^\s\[#]", rest, re.M):
        path.write_text(rest, encoding="utf-8", newline="\n")
    else:
        path.unlink()

def files(root):
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}

def kept(path):
    """Files a deploy does not replace: local/, metadata/local.meta and users/."""
    return path.parts[0] in ("local", "users") or path.parts[:2] == ("metadata", "local.meta")

def merge_local(root):
    """Merge local configuration into default files with ksconf and copy other local files."""
    from ksconf.conf.merge import merge_conf_dicts
    from ksconf.conf.parser import DUP_MERGE, PARSECONF_MID, ConfParserException, parse_conf, write_conf
    # Splunk combines a stanza repeated in one file; the ksconf CLI rejects it.
    profile = {**PARSECONF_MID, "dup_stanza": DUP_MERGE}
    pairs = [(root / "local" / p, root / "default" / p) for p in sorted(files(root / "local"))]
    if (root / "metadata" / "local.meta").exists():
        pairs.append((root / "metadata" / "local.meta", root / "metadata" / "default.meta"))
    for local, default in pairs:
        default.parent.mkdir(parents=True, exist_ok=True)
        if local.suffix in (".conf", ".meta"):
            try:
                confs = [parse_conf(p, profile=profile) for p in (default, local) if p.exists()]
            except ConfParserException as error:
                raise SystemExit(str(error))
            write_conf(default, merge_conf_dicts(*confs))
        else:
            shutil.copy2(local, default)
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

def file_changes(target, source, wanted):
    t, s = files(target), files(source)
    changes = []
    for p in sorted(p for p in t | s if wanted(p)):
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

def percent_changed(old, new):
    """Share of lines added or removed, ignoring line order."""
    a, b = Counter(old), Counter(new)
    pct = 100 * ((a - b).total() + (b - a).total()) / max(len(old) + len(new), 1)
    return "<1%" if 0 < pct < 1 else f"{pct:.0f}%"

def change_tree(changes, target, source):
    """Indented tree of changed files with line counts, target -> source."""
    lines, folders = [], set()
    for status, path in changes:
        for depth in range(1, len(path.parts)):
            folder = path.parts[:depth]
            if folder not in folders:
                lines.append("  " * (depth - 1) + f"{path.parts[depth - 1]}/")
                folders.add(folder)
        sides = [f.read_bytes().splitlines() for f in (target / path, source / path) if f.exists()]
        size = " -> ".join(str(len(side)) for side in sides) + " lines"
        if len(sides) == 2:
            size = f"{percent_changed(*sides)} ({size})"
        lines.append("  " * (len(path.parts) - 1) + f"{path.name} [{status.lower()}] {size}")
    return "\n".join(lines) or "NO DIFFERENCES"

def summary(target, source, target_before, source_before):
    changes = file_changes(target, source, deployed)
    deployed_list = [f"- {status}: {path.as_posix()}" for status, path in changes]
    return "\n".join([
        "## Deployed changes", *(deployed_list or ["NO DIFFERENCES"]),
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

def write_html_diff(app, target, source, changes, out):
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
    page += f"<h1>{html.escape(app)} deployed diff</h1><pre>{html.escape(change_tree(changes, target, source))}</pre>"
    page += tables or "<p>No deployed file changes.</p>"
    page += "</body></html>\n"
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
        name = local.relative_to(target).as_posix()
        subset.write_text("")
        filters = [["ksconf", "filter", str(local), "--brief", "-o", str(stanzas)]]
        if default.exists():
            filters.append(["ksconf", "filter", str(default), "--match", "string", "--stanza",
                            f"file://{stanzas}", "-o", str(subset)])
        failed = next((r for r in (run(f, capture_output=True, text=True) for f in filters) if r.returncode), None)
        if failed:
            detail = " ".join(failed.stderr.split())
            report.append((name, "Skipped", f"ksconf could not parse a file: {detail}"))
            continue
        # ksconf diff output and exit code report file differences.
        result = run(["ksconf", "diff", str(local), str(subset)], capture_output=True, text=True)
        status = "Changed" if result.stdout else "Unchanged"
        report.append((name, status, result.stdout))
    return report

def each_app(target_dir, source_dir, out_dir):
    """Yield app id, extracted target and source folders, and the output folder for every app."""
    targets, sources = archives(target_dir), archives(source_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    apps = sorted(targets.keys() | sources.keys())
    if not apps:
        log("section", "Target vs source")
        print_colored_patch("NO DIFFERENCES")
    for app in apps:
        log("section", f"{app}: target vs source")
        with tempfile.TemporaryDirectory() as tmp:
            target, source = Path(tmp, "target"), Path(tmp, "source")
            extract(targets.get(app), target)
            extract(sources.get(app), source)
            yield app, target, source, out, app in targets

def local_diff(target_dir, source_dir, out_dir):
    """Compare each target local file with the same stanzas in the source default file."""
    for app, target, source, out, _ in each_app(target_dir, source_dir, out_dir):
        work = target.with_name("local-vs-default")
        work.mkdir()
        reports = local_vs_default(target, source, work)
        shown = [r for r in reports if r[1] != "Unchanged"]
        text = "\n\n".join(f"{path} ({status})\n{report.rstrip()}" for path, status, report in shown)
        (out / f"{app}-local-vs-default.diff").write_text((text or "NO DIFFERENCES") + "\n", encoding="utf-8")
        for path, status, report in shown:
            print_file_banner(path, status)
            if status == "Skipped":
                log("warning", f"{path}: ksconf could not parse a file; skipped")
            print_colored_patch(report)
        if not shown:
            print_colored_patch("NO DIFFERENCES")

def print_file_banner(path, status):
    rule = "=" * 100
    print("\n\n")
    for line in (rule, f"{path} ({status})", rule):
        log("section", line)

def tree(target_dir, source_dir, out_dir):
    """Write and print the tree of raw target and source app files."""
    for app, target, source, out, _ in each_app(target_dir, source_dir, out_dir):
        changes = file_changes(target, source, lambda _: True)
        text = change_tree(changes, target, source) + "\n"
        (out / f"{app}-tree.txt").write_text(text, encoding="utf-8")
        print_colored_patch(text)

def diff(target_dir, source_dir, out_dir):
    """Write each app's merged archive, default-only diffs, and Markdown summary."""
    for app, target, source, out, in_target in each_app(target_dir, source_dir, out_dir):
        target_before, source_before = files(target), files(source)
        merge_local(target)
        merge_local(source)
        changes = file_changes(target, source, deployed)
        text = summary(target, source, target_before, source_before)
        write_html_diff(app, target, source, changes, out)
        merged_archive(app, target if in_target else source, out / f"{app}-merged.tar.gz")
        patch = []
        for status, path in changes:
            old, new = (r / path for r in (target, source))
            file_patch = b"".join(difflib.diff_bytes(
                difflib.unified_diff,
                old.read_bytes().splitlines(keepends=True) if old.exists() else [],
                new.read_bytes().splitlines(keepends=True) if new.exists() else [],
                f"target/{path.as_posix()}".encode(), f"source/{path.as_posix()}".encode(),
            ))
            patch.append(file_patch)
            print_file_banner(path.as_posix(), status)
            print_colored_patch(file_patch)
        if not changes:
            print_colored_patch("NO DIFFERENCES")
        (out / f"{app}.patch").write_bytes(b"".join(patch) or b"NO DIFFERENCES\n")
        (out / f"{app}-summary.md").write_text(text, encoding="utf-8")
        print(f"##vso[task.uploadsummary]{(out / f'{app}-summary.md').resolve()}")
        print(text, end="")

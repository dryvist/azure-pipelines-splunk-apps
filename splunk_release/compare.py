"""Compare exported and packaged apps and write deployment reports."""

import csv
import difflib
import filecmp
import html
import io
import re
import shutil
import tarfile
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

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
    dest.mkdir()
    if archive:
        with tarfile.open(archive) as tar:
            names = [PurePosixPath(name).parts for name in tar.getnames()]
            strip = len({parts[0] for parts in names}) == 1 and any(len(parts) > 1 for parts in names)

            def member(info, path):
                parts = PurePosixPath(info.name).parts[1:] if strip else PurePosixPath(info.name).parts
                return tarfile.data_filter(info.replace(name="/".join(parts)), path) if parts else None

            tar.extractall(dest, filter=member)
    drop_install_checksum(dest)
    sort_csvs(dest)

def sort_csvs(root):
    """Sort the rows of every CSV file, keeping the first row as the header."""
    for path in sorted(root.rglob("*.csv")):
        lines = path.read_bytes().splitlines()
        rows = sorted(line for line in lines[1:] if line.strip())
        # shortcut: a CSV with line breaks inside quoted fields stays unsorted; parse records if that becomes common.
        if len(list(csv.reader(io.StringIO(path.read_text(encoding="utf-8", errors="replace"))))) != len(lines):
            continue
        if lines and lines[1:] != rows:
            path.write_bytes(b"\n".join(lines[:1] + rows) + b"\n")

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

def parse(path):
    """Parse a .conf or .meta file with ksconf; a missing file is empty."""
    from ksconf.conf.parser import DUP_MERGE, PARSECONF_MID, ConfParserException, parse_conf
    try:
        # Splunk combines a stanza repeated in one file; the ksconf CLI rejects it.
        return parse_conf(path, profile={**PARSECONF_MID, "dup_stanza": DUP_MERGE}) if path.exists() else {}
    except ConfParserException as error:
        raise SystemExit(str(error))

def merge_local(root):
    """Merge local configuration into default files with ksconf and copy other local files."""
    from ksconf.conf.merge import merge_conf_dicts
    from ksconf.conf.parser import write_conf
    pairs = [(root / "local" / p, root / "default" / p) for p in sorted(files(root / "local"))]
    if (root / "metadata" / "local.meta").exists():
        pairs.append((root / "metadata" / "local.meta", root / "metadata" / "default.meta"))
    for local, default in pairs:
        default.parent.mkdir(parents=True, exist_ok=True)
        if local.suffix in (".conf", ".meta"):
            write_conf(default, merge_conf_dicts(parse(default), parse(local)))
        else:
            shutil.copy2(local, default)
    sort_confs(root / "default")
    sort_confs(root / "metadata")

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

def same_text(a, b):
    """True when two files differ only in line endings, trailing spaces or trailing blank lines."""
    lines = [[line.rstrip() for line in f.read_bytes().rstrip().splitlines()] for f in (a, b)]
    return lines[0] == lines[1]

def file_changes(target, source, wanted):
    t, s = files(target), files(source)
    changes = []
    for p in sorted(p for p in t | s if wanted(p)):
        if p not in t:
            status = "Added"
        elif p not in s:
            status = "Removed"
        elif not filecmp.cmp(target / p, source / p, shallow=False) and not same_text(target / p, source / p):
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

def stanza_changes(old, new):
    """One line per added, removed or changed stanza, with the number of settings that differ."""
    from ksconf.conf.parser import GLOBAL_STANZA
    a, b = ({"(global)" if name is GLOBAL_STANZA else name: {k: v for k, v in keys.items() if not k.startswith("#")}
             for name, keys in parse(path).items()} for path in (old, new))
    lines = []
    for name in sorted(a.keys() | b.keys()):
        x, y = a.get(name, {}), b.get(name, {})
        if name in a and name in b and x == y:
            continue
        status = "added" if name not in a else "removed" if name not in b else "changed"
        count = sum(x.get(k) != y.get(k) for k in x.keys() | y.keys())
        lines.append(f"[{name}] [{status}] {count} settings")
    return lines

def summary(changes, target_before, source_before):
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

def ordered(target, source, reverse):
    """The (- side, + side) pair: target first, or source first when reverse is set."""
    return (source, target) if reverse else (target, source)

def local_vs_default(target, source, work, reverse=False):
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
        result = run(["ksconf", "diff", *map(str, ordered(local, subset, reverse))], capture_output=True, text=True)
        status = "Changed" if result.stdout else "Unchanged"
        report.append((name, status, result.stdout))
    return report

def each_app(target_dir, source_dir, out_dir, flags=()):
    """Yield app id, extracted target and source folders, and the output folder for every app."""
    unknown = set(flags) - {"--reverse", "--skip-lookups"}
    if unknown:
        raise SystemExit(f"Unknown option: {' '.join(sorted(unknown))}")
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
            if "--skip-lookups" in flags:
                print("lookups/ skipped on both sides")
                for root in (target, source):
                    shutil.rmtree(root / "lookups", ignore_errors=True)
            yield app, target, source, out, app in targets

def local_diff(target_dir, source_dir, out_dir, *flags):
    """Compare each target local file with the same stanzas in the source default file."""
    for app, target, source, out, _ in each_app(target_dir, source_dir, out_dir, flags):
        work = target.with_name("local-vs-default")
        work.mkdir()
        reports = local_vs_default(target, source, work, "--reverse" in flags)
        shown = [r for r in reports if r[1] != "Unchanged"]
        text = "\n\n".join(f"{path} ({status})\n{report.rstrip()}" for path, status, report in shown)
        (out / f"{app}-local-vs-default.diff").write_text((text or "NO DIFFERENCES") + "\n", encoding="utf-8")
        for path, status, report in shown:
            if status == "Skipped":
                log("warning", f"{path}: ksconf could not parse a file; skipped")
            print_file_diff(path, status, report)
        if not shown:
            print_colored_patch("NO DIFFERENCES")

def print_file_diff(path, status, patch):
    """Print a separator, then the file's diff in a collapsed log group."""
    print("\n\n")
    log("section", "=" * 100)
    log("group", f"{path} ({status})")
    print_colored_patch(patch)
    log("endgroup")

def tree(target_dir, source_dir, out_dir, *flags):
    """Write and print the tree of raw target and source app files."""
    for app, target, source, out, _ in each_app(target_dir, source_dir, out_dir, flags):
        old, new = ordered(target, source, "--reverse" in flags)
        changes = file_changes(old, new, lambda _: True)
        text = change_tree(changes, old, new) + "\n"
        (out / f"{app}-tree.txt").write_text(text, encoding="utf-8")
        print_colored_patch(text)

def diff(target_dir, source_dir, out_dir, *flags):
    """Write each app's merged archive, default-only diffs, and Markdown summary."""
    for app, target, source, out, in_target in each_app(target_dir, source_dir, out_dir, flags):
        target_before, source_before = files(target), files(source)
        merge_local(target)
        merge_local(source)
        old, new = ordered(target, source, "--reverse" in flags)
        changes = file_changes(old, new, deployed)
        text = summary(changes, target_before, source_before)
        write_html_diff(app, old, new, changes, out)
        merged_archive(app, target if in_target else source, out / f"{app}-merged.tar.gz")
        confs = [(status, path) for status, path in changes if path.suffix in (".conf", ".meta")]
        stanzas = []
        log("section", "Changed stanzas")
        for status, path in confs:
            found = stanza_changes(old / path, new / path)
            stanzas.append("\n".join([path.as_posix(), *("  " + line for line in found)]))
            print_file_diff(path.as_posix(), f"{status}, {len(found)} stanzas", "\n".join(found))
        if not confs:
            print_colored_patch("NO DIFFERENCES")
        (out / f"{app}-stanzas.txt").write_text("\n\n".join(stanzas or ["NO DIFFERENCES"]) + "\n", encoding="utf-8")
        log("section", "Changed lines")
        patch = []
        for status, path in changes:
            a, b = (f.read_bytes().splitlines(keepends=True) if f.exists() else [] for f in (old / path, new / path))
            file_patch = b"".join(difflib.diff_bytes(
                difflib.unified_diff, a, b,
                f"target/{path.as_posix()}".encode(), f"source/{path.as_posix()}".encode(),
            ))
            patch.append(file_patch)
            size = f", {percent_changed(a, b)}" if status == "Changed" else ""
            print_file_diff(path.as_posix(), status + size, file_patch)
        if not changes:
            print_colored_patch("NO DIFFERENCES")
        (out / f"{app}.patch").write_bytes(b"".join(patch) or b"NO DIFFERENCES\n")
        (out / f"{app}-summary.md").write_text(text, encoding="utf-8")
        print(f"##vso[task.uploadsummary]{(out / f'{app}-summary.md').resolve()}")
        print(text, end="")

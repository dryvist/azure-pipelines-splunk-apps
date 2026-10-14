#!/usr/bin/env python3
"""Release, compare, and tag the Splunk app stored in ./package.

release.py bump                         update app.conf and app.manifest, then push the PR version (CI only)
release.py package                      stage package/ and write dist/<app-id>-<version>.tar.gz
release.py appinspect <dir>             submit the package in <dir> to AppInspect
release.py deploy <dir>                 install the single .tar.gz in <dir> with the ACS CLI
release.py status                       report current-stack status and pending restart
release.py wait-version <dir>           wait until ACS reports the packaged app version
release.py restart                      restart current-stack and wait for completion
release.py export <out-dir> [app-id...] export app data, custom apps (--custom), or a package directory
release.py diff <target> <source> <out> merge local, compare defaults, write artifacts
release.py install-acs                  download, verify, and add the ACS CLI for this agent to PATH
release.py appinspect-link              print the link to this build's published artifacts
release.py plan                         print which stages this run executes and why
release.py tag                          tag HEAD as v<version>, push the tag, and set APP_ID/APP_VERSION (CI only)

The ACS CLI reads STACK_TOKEN. Azure Pipelines maps ACS_TOKEN to STACK_TOKEN.
SPLUNK_SEARCH_HEAD selects a target search head for compare and smoke tests.
"""

import base64
import configparser
import difflib
import filecmp
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path

SRC = Path("package")
CONF = SRC / "default" / "app.conf"


def app_id():
    """Read the app id required by slim from app.conf [id] name; fall back to BUILD_REPOSITORY_NAME, then cwd."""
    conf = configparser.ConfigParser(interpolation=None, strict=False)
    conf.read(CONF, encoding="utf-8")
    return (
        conf.get("id", "name", fallback=None)
        or os.environ.get("BUILD_REPOSITORY_NAME")
        or Path.cwd().name
    )


APP = app_id()
MANIFEST = SRC / "app.manifest"
STAGE = Path("build") / APP
DIST = Path("dist")
TEXT = {
    "encoding": "utf-8",
    "newline": "",
}  # Preserve app.conf bytes except for version values.
VERSION_STANZAS = {"launcher", "id"}
# AppInspect result views: private_victoria approves Splunk Cloud (Victoria) private apps;
# future reports checks scheduled to become cloud vetting failures.
APPINSPECT_TAGS = "private_victoria,future"
# AppInspect rejects hidden files and compiled Python. Tests are excluded from the package.
EXCLUDE = shutil.ignore_patterns(".*", "__pycache__", "*.pyc", "*.pyo", "tests")


def bump_level(message):
    """Set the bump level from [major] or [minor] in the message; use patch otherwise."""
    message = message.lower()
    if "[major]" in message:
        return "major"
    if "[minor]" in message:
        return "minor"
    return "patch"


def bumped(version, level):
    major, minor, patch = map(int, version.split("."))
    return {
        "major": f"{major + 1}.0.0",
        "minor": f"{major}.{minor + 1}.0",
        "patch": f"{major}.{minor}.{patch + 1}",
    }[level]


def version_rows(lines):
    """Return {stanza: (line index, match)}; the [launcher] and [id] versions must match."""
    rows, section = {}, None
    for i, line in enumerate(lines):
        stanza = re.match(r"\s*\[(.+)\]", line)
        if stanza:
            section = stanza[1].strip()
            continue
        if section not in VERSION_STANZAS:
            continue
        version = re.match(r"(\s*version\s*=\s*)(\S+)", line)
        if version:
            rows[section] = (i, version)
    found = {section: match[2] for section, (_, match) in rows.items()}
    if set(found) != VERSION_STANZAS or len(set(found.values())) != 1:
        sys.exit(f"{CONF}: [launcher] and [id] need the same `version`, found {found}")
    return rows


def app_conf_version(text):
    _, match = version_rows(text.splitlines())["id"]
    return match[2]


def bump_conf(text, level):
    """Return updated text and version; preserve other text, including comments."""
    lines = text.splitlines(keepends=True)
    new = bumped(app_conf_version(text), level)
    for i, match in version_rows(lines).values():
        lines[i] = match[1] + new + lines[i][match.end() :]
    return "".join(lines), new


def sort_confs(root):
    """Sort stanzas and keys in every .conf file under root with ksconf, one blank line apart."""
    confs = sorted(str(p) for p in Path(root).rglob("*.conf"))
    if confs:
        # ksconf exits 9 when it rewrote a file.
        run(["ksconf", "sort", "--inplace", "--quiet", *confs], check=False)


def stage():
    """Copy package/ to build/<app>; slim requires the folder and tarball root to match the app id."""
    shutil.rmtree(STAGE.parent, ignore_errors=True)
    shutil.copytree(SRC, STAGE, ignore=EXCLUDE)


def run(cmd, **kwargs):
    """Print a command, then run it."""
    print("##[command]" + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, **kwargs)


def plan():
    """Print which stages this run executes and the rule behind each."""
    reason = os.environ.get("BUILD_REASON", "")
    branch = os.environ.get("BUILD_SOURCEBRANCH", "")
    pull_request, main = reason == "PullRequest", branch == "refs/heads/main"
    compare = pull_request or main
    print("##[section]Stage plan")
    print(f"Build.Reason = {reason}")
    print(f"Build.SourceBranch = {branch}")
    for stage, runs, rule in (
        ("build", True, "every run"),
        ("appinspect", True, "every run, after build"),
        ("nonprod", compare, "pull request or refs/heads/main"),
        ("proddiff", compare, "pull request or refs/heads/main"),
        ("release", main, "refs/heads/main, after proddiff"),
    ):
        print(f"{stage:<11} {'RUNS' if runs else 'SKIPPED':<8} runs when {rule}")


def install_acs():
    """Download, verify and unpack the ACS CLI for this agent, then add it to PATH."""
    asset, sha256 = {
        "posix": ("acs_v2.26.0_linux_amd64.tar.gz", "9450ee04be42c633af4b0db932d28139232815704bc4410c0908ea8ee38a8e49"),
        "nt": ("acs_v2.26.0_windows_amd64.zip", "062ab820347a7186c159f1e744fbc1b2f4d790c979cd4de1710a164abc22185e"),
    }[os.name]
    directory = Path(os.environ["AGENT_TEMPDIRECTORY"])
    archive = directory / asset
    url = f"https://github.com/splunk/acs-cli/releases/download/v2.26.0/{asset}"
    # curl uses the operating system's certificate store on Windows and Linux.
    run(["curl", "--fail", "--silent", "--show-error", "--location", "--output", str(archive), url], check=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != sha256:
        sys.exit(f"ACS CLI checksum mismatch: expected {sha256}, got {actual}")
    shutil.unpack_archive(archive, directory)
    print(f"##vso[task.prependpath]{directory}", flush=True)


def appinspect_link():
    """Print the link to this build's published artifacts."""
    print(
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECTID']}/_build/results"
        f"?buildId={os.environ['BUILD_BUILDID']}&view=artifacts&pathAsName=false&type=publishedArtifacts"
    )


def slim(*args):
    # slim loads this environment into a case-insensitive ConfigParser and fails when keys
    # differ only by case, such as SHELL and shell. Pass one entry per case-folded key.
    env = dict({k.lower(): (k, v) for k, v in os.environ.items()}.values())
    run(["slim", *args], check=True, env=env)


def git(*args):
    identity = [
        "-c",
        "user.name=Azure Pipelines",
        "-c",
        "user.email=azure-pipelines@localhost",
    ]
    run(["git", *identity, *args], check=True)


def bump():
    target_ref = os.environ.get("SYSTEM_PULLREQUEST_TARGETBRANCH")
    if not target_ref:
        print("not a PR validation build, skipping bump")
        return
    source_ref = os.environ.get("SYSTEM_PULLREQUEST_SOURCEBRANCH")
    if (
        not source_ref
        or not target_ref.startswith("refs/heads/")
        or not source_ref.startswith("refs/heads/")
    ):
        sys.exit(
            "SYSTEM_PULLREQUEST_TARGETBRANCH and SYSTEM_PULLREQUEST_SOURCEBRANCH must be refs/heads/... values"
        )
    target = target_ref.removeprefix("refs/heads/")
    source = source_ref.removeprefix("refs/heads/")
    git(
        "fetch",
        "origin",
        f"+refs/heads/{target}:refs/remotes/origin/{target}",
        f"+refs/heads/{source}:refs/remotes/origin/{source}",
    )
    # PR builds use a detached merge commit. The bump updates and pushes the PR source branch.
    git("checkout", "-B", source, f"origin/{source}")
    sort_confs(SRC)
    try:
        target_text = subprocess.check_output(
            ["git", "show", f"origin/{target}:{CONF.as_posix()}"], text=True
        )
    except subprocess.CalledProcessError:
        print("target app.conf is missing, skipping bump")
        return
    text = CONF.read_text(**TEXT)
    if app_conf_version(text) != app_conf_version(target_text):
        print("version already changed, skipping bump")
        return
    text, new = bump_conf(
        text, bump_level(os.environ.get("BUILD_SOURCEVERSIONMESSAGE", ""))
    )
    CONF.write_text(text, **TEXT)
    stage()
    # A new manifest ends with commented template lines and is invalid JSON. --update writes valid JSON.
    if not (STAGE / MANIFEST.name).exists():
        slim("generate-manifest", str(STAGE), "-o", str(STAGE / MANIFEST.name))
    slim("generate-manifest", "--update", str(STAGE), "-o", str(MANIFEST))
    git("add", str(SRC), str(MANIFEST))
    git("commit", "-m", f"Release {APP} {new}")
    git("push", "origin", f"HEAD:{source_ref}")
    print(f"{APP} bumped to {new}")


def package():
    shutil.rmtree(DIST, ignore_errors=True)
    sort_confs(SRC)
    stage()
    DIST.mkdir(parents=True, exist_ok=True)
    slim("package", str(STAGE), "-o", str(DIST))


def tag():
    """Tag HEAD as v<version>; git refuses a push if the tag points to another commit."""
    version = app_conf_version(CONF.read_text(**TEXT))
    git("tag", "--force", f"v{version}")
    git("push", "origin", f"refs/tags/v{version}")
    # The package feed step reads these.
    print(f"##vso[task.setvariable variable=APP_ID]{APP.lower()}")
    print(f"##vso[task.setvariable variable=APP_VERSION]{version}")


def http(url, headers, data=None, timeout=900):
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    print(f"##[command]{req.get_method()} {url}", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}\n{e.read().decode(errors='replace')}")


def appinspect_token():
    basic = base64.b64encode(
        f"{os.environ['SPLUNK_USERNAME']}:{os.environ['SPLUNK_PASSWORD']}".encode()
    ).decode()
    return json.loads(
        http(
            "https://api.splunk.com/2.0/rest/login/splunk",
            {"Authorization": f"Basic {basic}"},
        )
    )["data"]["token"]


def appinspect_passed(status, report):
    """Return true only for SUCCESS with zero failures, errors, and manual checks."""
    summary = report.get("summary", {})
    return (
        status == "SUCCESS"
        and summary.get("failure") == 0
        and summary.get("error") == 0
        and summary.get("manual_check") == 0
    )


def save_appinspect_report(artifact_dir, html, report):
    Path(artifact_dir, "appinspect-report.html").write_bytes(html)
    Path(artifact_dir, "appinspect-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


def appinspect(artifact_dir):
    pkg, _, _ = package_identity(artifact_dir)
    auth = {"Authorization": f"Bearer {appinspect_token()}"}
    content_type, body = multipart(pkg)
    response = json.loads(
        http(
            "https://appinspect.splunk.com/v1/app/validate",
            {**auth, "Content-Type": content_type},
            body,
        )
    )
    request_id = response["request_id"]
    tags = f"?included_tags={APPINSPECT_TAGS}"
    status_url = f"https://appinspect.splunk.com/v1/app/validate/status/{request_id}{tags}"
    deadline = time.monotonic() + 30 * 60
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sys.exit("AppInspect timed out after 30 minutes")
        status_body = http(
            status_url, {**auth, "Accept": "application/json"}, timeout=min(900, remaining)
        )
        status = json.loads(status_body)["status"]
        if status != "PROCESSING":
            break
        time.sleep(min(15, remaining))
    report_url = f"https://appinspect.splunk.com/v1/app/report/{request_id}{tags}"
    html = http(report_url, {**auth, "Accept": "text/html"})
    report = json.loads(
        http(
            report_url,
            {**auth, "Accept": "application/json"},
        )
    )
    save_appinspect_report(artifact_dir, html, report)
    summary = report.get("summary", {})
    print(
        f"AppInspect {status}: {json.dumps(summary, separators=(',', ':'), sort_keys=True)}"
    )
    if summary.get("future_failure"):
        print(
            "##vso[task.logissue type=warning]AppInspect future_failure: "
            f"{summary['future_failure']} checks will become cloud vetting failures"
        )
    if not appinspect_passed(status, report):
        sys.exit("AppInspect did not pass")


def configured_value(name):
    """Return a configured environment value, ignoring empty Azure placeholders."""
    value = os.environ.get(name, "").strip()
    return value if value and not value.startswith("$(") else None


def acs(env, *args):  # run an ACS CLI command, print its output in a ##[group], return stdout
    print(f"##[group]acs {' '.join(args)}")
    try:
        result = run(["acs", *args], capture_output=True, text=True, check=True, env=env)
    finally:
        result = locals().get("result", sys.exc_info()[1])
        print(getattr(result, "stdout", "") or "", getattr(result, "stderr", "") or "", sep="\n")
        print("##[endgroup]")
    return result.stdout


@contextmanager
def acs_session():
    """Select the configured stack and search head, then log in with STACK_TOKEN."""
    stack = os.environ["SPLUNK_STACK"]
    search_head = configured_value("SPLUNK_SEARCH_HEAD")
    with tempfile.TemporaryDirectory() as home:
        env = {**os.environ, "HOME": home, "USERPROFILE": home}
        print(f"##[section]ACS stack {stack}, search head {search_head or 'not set (all search heads)'}")
        target = [f"--target-sh={search_head}"] if search_head else []
        acs(env, "config", "add-stack", stack, "--use", *target)
        acs(env, "login")
        yield env


def restart_required(env):
    # shortcut: matches the documented restartRequired field; parse JSON if ACS changes format
    return bool(re.search(r'"restartRequired"\s*:\s*true', acs(env, "status", "current-stack", "-f", "structured"), re.I))


def status():
    with acs_session() as env:
        if restart_required(env):
            print(f"##[warning]Restart required on {os.environ['SPLUNK_STACK']}")


def package_identity(directory):
    packages = list(Path(directory).glob("*.tar.gz"))
    if len(packages) != 1:
        sys.exit(f"Expected one .tar.gz package in {directory}, found {len(packages)}")
    package = packages[0]
    app, _, version = package.name.removesuffix(".tar.gz").rpartition("-")
    if not app or not version:
        sys.exit(f"Expected <app-id>-<version>.tar.gz package name, found {package.name}")
    return package, app, version


def wait_version(directory):
    _, app, version = package_identity(directory)
    deadline = time.monotonic() + 300
    with acs_session() as env:
        while time.monotonic() < deadline:
            if version in acs(env, "apps", "describe", app):
                return
            time.sleep(min(3, max(0, deadline - time.monotonic())))
    print(f"##[error]Timed out after 300 seconds waiting for {app} version {version}")
    raise SystemExit(1)


def restart():
    with acs_session() as env:
        acs(env, "restart", "current-stack")
        deadline = time.monotonic() + 30 * 60
        while time.monotonic() < deadline:
            if not restart_required(env):
                return
            time.sleep(min(30, max(0, deadline - time.monotonic())))
    print("##[error]Timed out after 30 minutes waiting for restart completion")
    raise SystemExit(1)


def deploy(directory):
    package, app, version = package_identity(directory)
    print(f"##[section]Installing {app} {version} as a private app")
    with acs_session() as env:
        acs(env, "apps", "install", "private", "--acs-legal-ack", "Y", "--app-package", str(package))


def listed_apps(env, splunkbase=False):
    apps, offset = [], 0
    while True:
        args = ["apps", "list", "--count", "100", "--offset", str(offset)]
        if splunkbase:
            args.append("--splunkbase=true")
        raw = acs(env, *args, "-f", "structured")
        try:
            rows = json.loads(raw)["apps"]
            if not isinstance(rows, list):
                raise TypeError
        except (json.JSONDecodeError, KeyError, TypeError):
            print(raw)
            print("##[error]Missing apps in ACS output")
            raise SystemExit(1)
        apps.extend(item["name"] for item in rows)
        if len(rows) < 100:
            return apps
        offset += 100


def export(out_dir, *app_ids):
    package_dir = len(app_ids) == 1 and Path(app_ids[0]).is_dir()
    custom = app_ids == ("--custom",)
    out, apps = Path(out_dir), app_ids or [APP]
    if package_dir:
        _, app, _ = package_identity(app_ids[0])
        apps = [app]
        out /= app
        print(f"##vso[task.setvariable variable=APP_ID]{app}")

    out.mkdir(parents=True, exist_ok=True)
    apps_file = out / "apps.json"
    try:
        with acs_session() as env:
            if custom:
                installed = listed_apps(env)
                splunkbase = {app.casefold() for app in listed_apps(env, True)}
                apps = sorted({app for app in installed if app.casefold() not in splunkbase})
            for app in apps:
                apps_file.write_text(json.dumps({"Apps": [app]}))
                acs(env, "apps", "export", f"--file={apps_file}", "--default=true", "--local=true",
                    "--users=true", "--confs-only=false", f"--export-dir={out}")
                exported = out / f"{app}.tar.gz"
                if exported.exists():
                    exported.rename(out / f"{app}.tgz")
                else:
                    print(f"##[warning]NOT INSTALLED {app}")
    finally:
        apps_file.unlink(missing_ok=True)


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


def print_colored_patch(patch):
    colors = {"+": "\033[32m", "-": "\033[31m", "@": "\033[36m"}
    for line in patch.decode("utf-8", "replace").splitlines():
        color = None
        if line.startswith("@@"):
            color = colors["@"]
        elif line.startswith("+") and not line.startswith("+++"):
            color = colors["+"]
        elif line.startswith("-") and not line.startswith("---"):
            color = colors["-"]
        print(f"{color}{line}\033[0m" if color else line)


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


def multipart(pkg):
    """Build (content_type, body) for a multipart/form-data POST with app_package."""
    boundary = uuid.uuid4().hex
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="app_package"; '
        f'filename="{pkg.name}"\r\nContent-Type: application/gzip\r\n\r\n'
    )
    body = head.encode() + pkg.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return f"multipart/form-data; boundary={boundary}", body


if __name__ == "__main__":
    commands = {
        "bump": bump,
        "package": package,
        "appinspect": appinspect,
        "deploy": deploy,
        "status": status,
        "wait-version": wait_version,
        "restart": restart,
        "plan": plan,
        "export": export,
        "diff": diff,
        "install-acs": install_acs,
        "appinspect-link": appinspect_link,
        "tag": tag,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])

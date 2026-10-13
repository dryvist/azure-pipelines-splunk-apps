#!/usr/bin/env python3
"""Release, compare, and tag the Splunk app stored in ./package.

release.py bump                         update app.conf and app.manifest, then push the PR version (CI only)
release.py package                      stage package/ and write dist/<app-id>-<version>.tar.gz
release.py appinspect <dir>             submit the package in <dir> to AppInspect
release.py deploy <dir>                 install the single .tar.gz in <dir> with the ACS CLI
release.py export <out-dir> [app-id...] export default, local, and users data for each app (default: this app) as <app-id>.tgz
release.py diff <target> <source> <out> merge local, compare defaults, write artifacts
release.py tag                          tag HEAD as v<version>, push the tag, and set APP_ID/APP_VERSION (CI only)

The ACS CLI reads STACK_TOKEN. Azure Pipelines maps ACS_TOKEN to STACK_TOKEN.
SPLUNK_SEARCH_HEAD selects a target search head. Installs to that target use
the local scope.
"""

import base64
import configparser
import filecmp
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


def stage():
    """Copy package/ to build/<app>; slim requires the folder and tarball root to match the app id."""
    shutil.rmtree(STAGE.parent, ignore_errors=True)
    shutil.copytree(SRC, STAGE, ignore=EXCLUDE)


def slim(*args):
    # slim loads this environment into a case-insensitive ConfigParser and fails when keys
    # differ only by case, such as SHELL and shell. Pass one entry per case-folded key.
    env = dict({k.lower(): (k, v) for k, v in os.environ.items()}.values())
    subprocess.run(["slim", *args], check=True, env=env)


def git(*args):
    identity = [
        "-c",
        "user.name=Azure Pipelines",
        "-c",
        "user.email=azure-pipelines@localhost",
    ]
    subprocess.run(["git", *identity, *args], check=True)


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
    git("add", str(CONF), str(MANIFEST))
    git("commit", "-m", f"Release {APP} {new}")
    git("push", "origin", f"HEAD:{source_ref}")
    print(f"{APP} bumped to {new}")


def package():
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
    (pkg,) = Path(artifact_dir).glob("*.tar.gz")
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


@contextmanager
def acs_session():
    """Select the configured stack and search head, then log in with STACK_TOKEN."""
    stack = os.environ["SPLUNK_STACK"]
    search_head = configured_value("SPLUNK_SEARCH_HEAD")
    with tempfile.TemporaryDirectory() as home:
        env = {**os.environ, "HOME": home}
        subprocess.run(["acs", "config", "add-stack", stack, "--use"], check=True, env=env)
        if search_head:
            subprocess.run(
                ["acs", "config", "use-stack", stack, f"--target-sh={search_head}"],
                check=True,
                env=env,
            )
        subprocess.run(["acs", "login"], check=True, env=env)
        yield env


def deploy(artifact_dir):
    (pkg,) = Path(artifact_dir).glob("*.tar.gz")
    with acs_session() as env:
        cmd = ["acs", "apps", "install", "private", "--acs-legal-ack", "Y", "--app-package", str(pkg)]
        if configured_value("SPLUNK_SEARCH_HEAD"):
            cmd.extend(["--scope", "local"])
        subprocess.run(cmd, check=True, env=env)


def export(out_dir, *app_ids):
    """Save each app as <out_dir>/<app-id>.tgz with default, local and users content."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    apps_file = out / "apps.json"
    with acs_session() as env:
        for app in app_ids or [APP]:
            apps_file.write_text(json.dumps({"Apps": [app]}))
            cmd = ["acs", "apps", "export", f"--file={apps_file}", "--default=true", "--local=true",
                   "--users=true", "--confs-only=false", f"--export-dir={out}"]
            subprocess.run(cmd, check=False, env=env)
            if not (out / f"{app}.tgz").exists():
                print(f"NOT INSTALLED {app}")
    apps_file.unlink()


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


def summary(target, source, target_before, source_before):
    t, s = files(target), files(source)
    changes = []
    for p in sorted(p for p in t | s if deployed(p)):
        if p not in t:
            changes.append(f"- Added: {p.as_posix()}")
        elif p not in s:
            changes.append(f"- Removed: {p.as_posix()}")
        elif not filecmp.cmp(target / p, source / p, shallow=False):
            changes.append(f"- Changed: {p.as_posix()}")
    return "\n".join([
        "## Deployed changes", *(changes or ["- None"]),
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


def diff(target_dir, source_dir, out_dir):
    """Write each app's merged archive, deployed patch, and Markdown summary."""
    targets, sources = archives(target_dir), archives(source_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for app in sorted(targets.keys() | sources.keys()):
        with tempfile.TemporaryDirectory() as tmp:
            target, source = Path(tmp, "target"), Path(tmp, "source")
            extract(targets.get(app), target)
            extract(sources.get(app), source)
            target_before, source_before = files(target), files(source)
            merge_local(target)
            merge_local(source)
            text = summary(target, source, target_before, source_before)
            merged_archive(app, target if app in targets else source,
                           out / f"{app}-merged.tar.gz")
            for root in (target, source):
                for p in files(root):
                    if not deployed(p):
                        (root / p).unlink()
            # diff exits 1 when the trees differ, 2 on error.
            patch = subprocess.run(["diff", "-ruN", "target", "source"], cwd=tmp,
                                   capture_output=True, text=True, check=False)
            if patch.returncode > 1:
                sys.exit(f"diff failed for {app}: {patch.stderr}")
        (out / f"{app}.patch").write_text(patch.stdout, encoding="utf-8")
        (out / f"{app}-summary.md").write_text(text, encoding="utf-8")
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
        "export": export,
        "diff": diff,
        "tag": tag,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])

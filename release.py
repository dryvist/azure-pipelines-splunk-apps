#!/usr/bin/env python3
"""Bump, package and deploy a Splunk app whose raw contents live in ./package.

release.py bump            bump app.conf, regenerate app.manifest, commit + push (CI only)
release.py package         write dist/<app>-<version>.tar.gz
release.py deploy <dir>    install the one .tar.gz in <dir> via ACS (SPLUNK_STACK, ACS_TOKEN,
                           SPLUNK_USERNAME, SPLUNK_PASSWORD from env)
release.py export <dir>    save the stack's installed app (default, local, users) as <dir>/<app>-prod.tgz
                           via the ACS app export (SPLUNK_STACK, ACS_TOKEN from env)
release.py diff <pkg-dir> <dir>
                           write <dir>/prod-diff.patch: the export in <dir> (if any) against the package
release.py tag             tag HEAD v<version>, push the tag and set APP_ID/APP_VERSION (CI only)
"""

import base64
import configparser
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

SRC = Path("package")
CONF = SRC / "default" / "app.conf"


def app_id():
    """[id] name in app.conf is the app id slim enforces; fall back to the repo name."""
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
}  # keep app.conf byte-for-byte except the versions
VERSION_STANZAS = {"launcher", "id"}
# AppInspect rejects hidden files and compiled Python; tests never ship.
EXCLUDE = shutil.ignore_patterns(".*", "__pycache__", "*.pyc", "*.pyo", "tests")


def bump_level(message):
    """[major] or [minor] anywhere in the commit message picks the level; patch otherwise."""
    return next(
        (lvl for lvl in ("major", "minor") if f"[{lvl}]" in message.lower()), "patch"
    )


def bumped(version, level):
    major, minor, patch = map(int, version.split("."))
    return {
        "major": f"{major + 1}.0.0",
        "minor": f"{major}.{minor + 1}.0",
        "patch": f"{major}.{minor}.{patch + 1}",
    }[level]


def version_rows(lines):
    """{stanza: (line index, match)} for the [launcher] and [id] version rows, which must match."""
    hits, section = {}, None
    for i, line in enumerate(lines):
        if m := re.match(r"\s*\[(.+)\]", line):
            section = m[1].strip()
        elif section in VERSION_STANZAS and (
            m := re.match(r"(\s*version\s*=\s*)(\S+)", line)
        ):
            hits[section] = (i, m)
    found = {s: m[2] for s, (_, m) in hits.items()}
    if found.keys() != VERSION_STANZAS or len(set(found.values())) != 1:
        sys.exit(f"{CONF}: [launcher] and [id] need the same `version`, found {found}")
    return hits


def app_conf_version(text):
    _, match = version_rows(text.splitlines())["id"]
    return match[2]


def bump_conf(text, level):
    """Return (text, new_version) with both versions bumped; everything else, comments included, untouched."""
    lines = text.splitlines(keepends=True)
    new = bumped(app_conf_version(text), level)
    for i, m in version_rows(lines).values():
        lines[i] = m[1] + new + lines[i][m.end() :]
    return "".join(lines), new


def stage():
    """Copy package/ to build/<app>/: slim requires the folder name to equal the app id, and the tarball root must too."""
    shutil.rmtree(STAGE.parent, ignore_errors=True)
    shutil.copytree(SRC, STAGE, ignore=EXCLUDE)


def slim(*args):
    # slim loads the environment into a case-insensitive ConfigParser and crashes on keys that
    # differ only by case (e.g. SHELL and shell). Hand it one entry per case-folded name.
    env = dict({k.lower(): (k, v) for k, v in os.environ.items()}.values())
    subprocess.run([sys.executable, "-m", "slim", *args], check=True, env=env)


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
    # PR builds check out a detached merge commit; bump and push the PR branch itself.
    git("checkout", "-B", source, f"origin/{source}")
    try:
        target_text = subprocess.check_output(
            ["git", "show", f"origin/{target}:{CONF.as_posix()}"], text=True
        )
    except subprocess.CalledProcessError:
        print("target app.conf is missing, skipping bump")
        return
    if app_conf_version(CONF.read_text(**TEXT)) != app_conf_version(target_text):
        print("version already changed, skipping bump")
        return
    text, new = bump_conf(
        CONF.read_text(**TEXT),
        bump_level(os.environ.get("BUILD_SOURCEVERSIONMESSAGE", "")),
    )
    CONF.write_text(text, **TEXT)
    stage()
    # A fresh manifest ends in commented-out template lines (not valid JSON); --update output is pure JSON.
    if not (STAGE / MANIFEST.name).exists():
        slim("generate-manifest", str(STAGE), "-o", str(STAGE / MANIFEST.name))
    slim("generate-manifest", "--update", str(STAGE), "-o", str(MANIFEST))
    git("add", str(CONF), str(MANIFEST))
    git("commit", "-m", f"Release {APP} {new}")
    git("push", "origin", f"HEAD:{source_ref}")
    print(f"{APP} bumped to {new}")


def normalize(info):
    """Deterministic, non-world-writable entries regardless of the agent OS."""
    info.mode = 0o755 if info.isdir() or info.mode & 0o100 else 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def package():
    stage()
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{APP}-{app_conf_version(CONF.read_text(**TEXT))}.tar.gz"
    with tarfile.open(out, "w:gz", format=tarfile.GNU_FORMAT) as tar:
        tar.add(STAGE, arcname=APP, filter=normalize)
    print(out)


def tag():
    """Tag HEAD v<version>; git refuses the push when that tag already points at another commit."""
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
    """AppInspect is green only when the job and its failure/error counts pass."""
    summary = report.get("summary", {})
    return (
        status == "SUCCESS"
        and summary.get("failure") == 0
        and summary.get("error") == 0
    )


def save_appinspect_report(artifact_dir, html, report):
    Path(artifact_dir, "appinspect-report.html").write_bytes(html)
    report_text = json.dumps(report, indent=2)
    Path(artifact_dir, "appinspect-report.json").write_text(
        report_text + "\n", encoding="utf-8"
    )
    print(report_text)


def appinspect(artifact_dir):
    (pkg,) = Path(artifact_dir).glob("*.tar.gz")
    token = appinspect_token()
    content_type, body = multipart(pkg)
    response = json.loads(
        http(
            "https://appinspect.splunk.com/v1/app/validate",
            {"Authorization": f"Bearer {token}", "Content-Type": content_type},
            body,
        )
    )
    request_id = response["request_id"]
    status_url = f"https://appinspect.splunk.com/v1/app/validate/status/{request_id}"
    deadline = time.monotonic() + 30 * 60
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sys.exit("AppInspect timed out after 30 minutes")
        status_body = http(
            status_url, {"Accept": "application/json"}, timeout=min(900, remaining)
        )
        status = json.loads(status_body)["status"]
        if status != "PROCESSING":
            break
        time.sleep(min(15, remaining))
    report_url = f"https://appinspect.splunk.com/v1/app/report/{request_id}"
    html = http(report_url, {"Content-Type": "text/html", "Accept": "text/html"})
    report = json.loads(
        http(
            report_url,
            {"Content-Type": "application/json", "Accept": "application/json"},
        )
    )
    save_appinspect_report(artifact_dir, html, report)
    summary = report.get("summary", {})
    print(
        f"AppInspect {status}: {json.dumps(summary, separators=(',', ':'), sort_keys=True)}"
    )
    if not appinspect_passed(status, report):
        sys.exit("AppInspect did not pass")


def deploy(artifact_dir):
    (pkg,) = Path(artifact_dir).glob("*.tar.gz")
    token = appinspect_token()
    url = f"https://admin.splunk.com/{os.environ['SPLUNK_STACK']}/adminconfig/v2/apps/victoria"
    headers = {
        "Authorization": f"Bearer {os.environ['ACS_TOKEN']}",
        "X-Splunk-Authorization": token,
        "ACS-Legal-Ack": "Y",
    }
    print(http(url, headers, pkg.read_bytes()).decode())


def export(out_dir):
    """Save the app as installed on SPLUNK_STACK, including local and users content."""
    url = (
        f"https://admin.splunk.com/{os.environ['SPLUNK_STACK']}/adminconfig/v2/apps/victoria/"
        f"export/download/{APP}?default=true&local=true&users=true"
    )
    body = http(url, {"Authorization": f"Bearer {os.environ['ACS_TOKEN']}"})
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(out_dir, f"{APP}-prod.tgz").write_bytes(body)


def diff(pkg_dir, out_dir):
    out = Path(out_dir)
    trees = out / "trees"
    archives = {
        "prod": out / f"{APP}-prod.tgz",
        "new": next(Path(pkg_dir).glob("*.tar.gz")),
    }
    for name, archive in archives.items():
        (trees / name).mkdir(parents=True)
        # shortcut: assumes the export's root folder is the app id, like the package; if not,
        # every path differs by that folder. Strip it here once a real export shows otherwise.
        if archive.exists():
            with tarfile.open(archive) as tar:
                tar.extractall(trees / name, filter="data")
    # diff exits 1 when the trees differ, 2 on error.
    patch = subprocess.run(
        ["diff", "-ruN", "prod", "new"],
        cwd=trees,
        capture_output=True,
        text=True,
        check=False,
    )
    if patch.returncode > 1:
        sys.exit(f"diff failed: {patch.stderr}")
    (out / "prod-diff.patch").write_text(patch.stdout, encoding="utf-8")
    print("Changed files:", flush=True)
    subprocess.run(["diff", "-rq", "prod", "new"], cwd=trees, check=False)
    shutil.rmtree(trees)


def multipart(pkg):
    """(content_type, body) for a multipart/form-data POST of the package as app_package."""
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

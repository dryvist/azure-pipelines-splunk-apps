#!/usr/bin/env python3
"""Bump, package and deploy a Splunk app whose raw contents live in ./package.

release.py bump            bump app.conf, regenerate app.manifest, commit + push (CI only)
release.py package         write dist/<app>-<version>.tar.gz
release.py deploy <dir>    install the one .tar.gz in <dir> via ACS (SPLUNK_STACK, ACS_TOKEN,
                           SPLUNK_USERNAME, SPLUNK_PASSWORD, optional SPLUNK_EXPERIENCE from env)
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


def app_conf_version(text):
    """Read and validate the shared version with ConfigParser."""
    conf = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        conf.read_string(text)
    except configparser.Error as e:
        sys.exit(f"{CONF}: could not read app.conf: {e}")
    found = {
        section: conf.get(section, "version")
        for section in VERSION_STANZAS
        if conf.has_option(section, "version")
    }
    if found.keys() != VERSION_STANZAS or len(set(found.values())) != 1:
        sys.exit(f"{CONF}: [launcher] and [id] need the same `version`, found {found}")
    return found["id"]


def version_lines(lines):
    """[(line index, match)] for version rows; keep the rest of app.conf byte-for-byte."""
    app_conf_version("\n".join(line.rstrip("\r\n") for line in lines))
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
    return list(hits.values())


def current_version(lines):
    return app_conf_version("\n".join(line.rstrip("\r\n") for line in lines))


def bump_conf(text, level):
    """Return (text, new_version) with both versions bumped; everything else, comments included, untouched."""
    lines = text.splitlines(keepends=True)
    new = bumped(current_version(lines), level)
    for i, m in version_lines(lines):
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
    subprocess.run(["git", *args], check=True)


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
    if current_version(CONF.read_text(**TEXT).splitlines()) != current_version(
        target_text.splitlines()
    ):
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
    git(
        "-c",
        "user.name=Azure Pipelines",
        "-c",
        "user.email=azure-pipelines@localhost",
        "commit",
        "-m",
        f"Release {APP} {new}",
    )
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
    out = DIST / f"{APP}-{current_version(CONF.read_text(**TEXT).splitlines())}.tar.gz"
    with tarfile.open(out, "w:gz", format=tarfile.GNU_FORMAT) as tar:
        tar.add(STAGE, arcname=APP, filter=normalize)
    print(out)


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
    fields = {"app_package": pkg}
    if tags := os.environ.get("APPINSPECT_TAGS"):
        fields["included_tags"] = tags
    content_type, body = multipart(**fields)
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

    def get_status():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sys.exit("AppInspect timed out after 30 minutes")
        return json.loads(
            http(
                status_url, {"Accept": "application/json"}, timeout=min(900, remaining)
            )
        )["status"]

    status = get_status()
    while status == "PROCESSING":
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sys.exit("AppInspect timed out after 30 minutes")
        time.sleep(min(15, remaining))
        status = get_status()
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
    url = f"https://admin.splunk.com/{os.environ['SPLUNK_STACK']}/adminconfig/v2/apps"
    headers = {
        "Authorization": f"Bearer {os.environ['ACS_TOKEN']}",
        "ACS-Legal-Ack": "Y",
    }
    # Victoria takes the raw package plus a token header; Classic takes a multipart form.
    if os.environ.get("SPLUNK_EXPERIENCE", "victoria").lower() == "classic":
        headers["Content-Type"], body = multipart(token=token, package=pkg)
    else:
        url += "/victoria"
        headers["X-Splunk-Authorization"] = token
        body = pkg.read_bytes()
    print(http(url, headers, body).decode())


def multipart(**fields):
    """(content_type, body) for a multipart/form-data POST; Path values are sent as files."""
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        if isinstance(value, Path):
            head = f'name="{name}"; filename="{value.name}"\r\nContent-Type: application/gzip'
            data = value.read_bytes()
        else:
            head, data = f'name="{name}"', value.encode()
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; {head}\r\n\r\n".encode()
            + data
            + b"\r\n"
        )
    return f"multipart/form-data; boundary={boundary}", b"".join(
        parts
    ) + f"--{boundary}--\r\n".encode()


if __name__ == "__main__":
    commands = {
        "bump": bump,
        "package": package,
        "appinspect": appinspect,
        "deploy": deploy,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](*sys.argv[2:])

"""App identity, version changes, and Git release operations."""

import configparser
import os
import re
import subprocess
import sys
from pathlib import Path

from splunk_release.azure import run

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

def git(*args):
    identity = [
        "-c",
        "user.name=Azure Pipelines",
        "-c",
        "user.email=azure-pipelines@localhost",
    ]
    run(["git", *identity, *args], check=True)

def bump():
    from splunk_release.package import slim, sort_confs, stage

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
    source_version, target_version = app_conf_version(text), app_conf_version(target_text)
    print(f"{source} app.conf version {source_version}, {target} app.conf version {target_version}")
    if source_version != target_version:
        print(f"{source} already changes the version, skipping bump")
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

def tag():
    """Tag HEAD as v<version>; git refuses a push if the tag points to another commit."""
    version = app_conf_version(CONF.read_text(**TEXT))
    git("tag", "--force", f"v{version}")
    git("push", "origin", f"refs/tags/v{version}")
    # The package feed step reads these.
    print(f"##vso[task.setvariable variable=APP_ID]{APP.lower()}")
    print(f"##vso[task.setvariable variable=APP_VERSION]{version}")

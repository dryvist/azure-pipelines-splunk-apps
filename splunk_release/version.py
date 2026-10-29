"""App identity, version changes, and Git release operations."""

import configparser
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from splunk_release.azure import http, log, run

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
    """Return {stanza: (line index, match)} for the [launcher] and [id] version rows."""
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
    return rows

def app_conf_version(text):
    """The highest of the [launcher] and [id] versions."""
    found = [match[2] for _, match in version_rows(text.splitlines()).values()]
    if not found:
        sys.exit(f"{CONF}: [launcher] and [id] have no `version`")
    return highest(*found)

def highest(*versions):
    """The highest x.y.z version."""
    return max(versions, key=lambda version: tuple(map(int, version.split("."))))

def bump_conf(text, level, *others):
    """Return updated text and a version above app.conf and others; preserve other text, including comments."""
    new = bumped(highest(app_conf_version(text), *others), level)
    return set_version(text, new), new

def set_version(text, version):
    """Set both app.conf version rows and preserve all other text."""
    lines = text.splitlines(keepends=True)
    rows = version_rows(lines)
    if set(rows) != VERSION_STANZAS:
        sys.exit(f"{CONF}: [launcher] and [id] both need a `version`")
    for i, match in rows.values():
        lines[i] = match[1] + version + lines[i][match.end() :]
    return "".join(lines)

def git(*args):
    identity = [
        "-c",
        "user.name=Azure Pipelines",
        "-c",
        "user.email=azure-pipelines@localhost",
    ]
    run(["git", *identity, *args], check=True)

def generate_manifest():
    """Regenerate package/app.manifest with the packaging toolkit."""
    from splunk_release.package import slim, stage

    stage()
    if not (STAGE / MANIFEST.name).exists():
        slim("generate-manifest", str(STAGE), "-o", str(STAGE / MANIFEST.name))
    slim("generate-manifest", "--update", str(STAGE), "-o", str(MANIFEST))

def bump():
    from splunk_release.package import app_conf_required, sort_confs

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
    # Check out the PR source branch before writing the bump commit.
    git("checkout", "-B", source, f"origin/{source}")
    sort_confs(SRC)
    app_conf_required(SRC, APP)
    target_path = f"origin/{target}:{CONF.as_posix()}"
    if subprocess.run(["git", "cat-file", "-e", target_path], capture_output=True).returncode:
        log("warning", "Target app.conf is missing, skipping bump")
        return
    target_text = run(["git", "show", target_path], check=True, capture_output=True, text=True).stdout
    text = CONF.read_text(**TEXT)
    source_version, target_version = app_conf_version(text), app_conf_version(target_text)
    log("section", "Compare source and target app versions")
    print(f"Source app.conf version {source_version}; target app.conf version {target_version}")
    message = f"Standardize {APP} app.conf"
    if source_version != target_version:
        print("Source version already differs, skipping bump")
    else:
        text, new = bump_conf(
            text, bump_level(os.environ.get("BUILD_SOURCEVERSIONMESSAGE", "")), *feed_versions(APP.lower())
        )
        CONF.write_text(text, **TEXT)
        message = f"Release {APP} {new}"
    if not subprocess.run(["git", "status", "--porcelain", "--", str(SRC)], capture_output=True, text=True).stdout:
        return
    generate_manifest()
    git("add", str(SRC), str(MANIFEST))
    git("commit", "-m", message)
    git("push", "origin", f"HEAD:{source_ref}")
    print(message)
    print("The bump commit starts the next validation run; this run stops here.")
    print("##vso[task.setvariable variable=bumped;isOutput=true]true")

def tag():
    """Tag HEAD as v<version>; git refuses a push if the tag points to another commit."""
    version = app_conf_version(CONF.read_text(**TEXT))
    git("tag", "--force", f"v{version}")
    git("push", "origin", f"refs/tags/v{version}")
    # Set the package feed variables.
    print(f"##vso[task.setvariable variable=APP_ID]{APP.lower()}")
    print(f"##vso[task.setvariable variable=APP_VERSION]{version}")
    if published(APP.lower(), version):
        print(f"{APP.lower()} {version} is already in the splunk-apps feed, skipping publish")
        print("##vso[task.setvariable variable=PACKAGE_PUBLISHED]true")

def published(name, version):
    """Return whether the splunk-apps feed already holds this package version."""
    return version in feed_versions(name)

def feed_check(name):
    """Exit with an error when the splunk-apps feed holds no version of this app."""
    name = name.lower()
    if not feed_versions(name):
        sys.exit(f"{name} is not in the splunk-apps feed; run its app pipeline on main to release it")
    print(f"{name} is in the splunk-apps feed")

def feed_missing(name):
    """Set the MISSING output variable to true when the splunk-apps feed holds no version of this app."""
    name = name.lower()
    missing = not feed_versions(name)
    print(f"{name} is {'not ' if missing else ''}in the splunk-apps feed")
    print(f"##vso[task.setvariable variable=MISSING;isOutput=true]{str(missing).lower()}")

def feed_versions(name):
    """Return every version the splunk-apps feed holds for this package name."""
    e = os.environ
    host = e["SYSTEM_COLLECTIONURI"].replace("://dev.azure.com/", "://feeds.dev.azure.com/")
    host = host.replace(".visualstudio.com/", ".feeds.visualstudio.com/")
    url = (f"{host}{e['SYSTEM_TEAMPROJECTID']}/_apis/packaging/feeds/splunk-apps/packages?protocolType=upack"
           f"&packageNameQuery={name}&includeAllVersions=true&api-version=7.1")
    body = http(url, {"Authorization": f"Bearer {e['SYSTEM_ACCESSTOKEN']}"})
    return [v["version"] for p in json.loads(body)["value"] if p["name"].lower() == name
            for v in p.get("versions", [])]

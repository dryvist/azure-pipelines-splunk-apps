"""Configure and operate the Splunk Cloud ACS CLI."""

import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from splunk_release.azure import log, run
from splunk_release.version import APP

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
    unpack_options = {}
    if (
        archive.suffix == ".gz"
        and "filter" in inspect.signature(shutil.unpack_archive).parameters
    ):
        unpack_options["filter"] = (
            "data" if sys.version_info >= (3, 14) else "fully_trusted"
        )
    shutil.unpack_archive(archive, directory, **unpack_options)
    print(f"##vso[task.prependpath]{directory}", flush=True)
    os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ['PATH']}"
    env = acs_env()
    Path(env["HOME"]).mkdir(exist_ok=True)
    stack, search_head = os.environ["SPLUNK_STACK"], configured_value("SPLUNK_SEARCH_HEAD")
    log("section", f"ACS stack {stack}, search head {search_head or 'not set (all search heads)'}")
    acs(env, "version")
    acs(env, "config", "add-stack", stack, "--use", *([f"--target-sh={search_head}"] if search_head else []))
    acs(env, "login")


def configured_value(name):
    """Return a configured environment value, ignoring empty Azure placeholders."""
    value = os.environ.get(name, "").strip()
    return value if value and not value.startswith("$(") else None

def acs(env, *args, main=False):
    """Run an ACS CLI command and return stdout; output is grouped unless main or failed."""
    if not main:
        log("group", f"acs {' '.join(args)}")
    result = run(["acs", *args], capture_output=True, text=True, env=env)
    if not main and result.returncode:
        log("endgroup")
    for output in (result.stdout, result.stderr):
        if output.strip():
            print(output.rstrip())
    if not main and not result.returncode:
        log("endgroup")
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result.stdout

def acs_env():
    """Environment whose HOME holds the ACS CLI configuration written by install-acs."""
    home = str(Path(os.environ["AGENT_TEMPDIRECTORY"]) / "acs-home")
    return {**os.environ, "HOME": home, "USERPROFILE": home}

def stack_status(env):
    """Return the decoded "response" JSON from the single object acs status prints."""
    raw = acs(env, "status", "current-stack", "-f", "structured")
    try:
        envelope = json.loads(raw)
        response = json.loads(envelope[0]["response"])
        if not isinstance(response, dict):
            raise ValueError("response must be an object")
        return response
    except (ValueError, IndexError, KeyError, TypeError):
        log("error", 'acs status output has no JSON "response" object')
        raise SystemExit(1)

def restart_required(response):
    return response.get("messages", {}).get("restartRequired") is True

def status():
    env = acs_env()
    response = stack_status(env)
    log("section", f"Stack status of {os.environ['SPLUNK_STACK']}")
    print(json.dumps(response, indent=2))
    if restart_required(response):
        log("warning", f"Restart required on {os.environ['SPLUNK_STACK']}")

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
    env = acs_env()
    while time.monotonic() < deadline:
        if version in acs(env, "apps", "describe", app):
            return
        time.sleep(min(3, max(0, deadline - time.monotonic())))
    log("error", f"Timed out after 300 seconds waiting for {app} version {version}")
    raise SystemExit(1)

def restart():
    env = acs_env()
    if not restart_required(stack_status(env)):
        log("section", f"No restart required on {os.environ['SPLUNK_STACK']}, skipping restart")
        return
    acs(env, "restart", "current-stack", main=True)
    deadline = time.monotonic() + 30 * 60
    while time.monotonic() < deadline:
        if not restart_required(stack_status(env)):
            return
        time.sleep(min(30, max(0, deadline - time.monotonic())))
    log("error", "Timed out after 30 minutes waiting for restart completion")
    raise SystemExit(1)

def deploy(directory):
    package, app, version = package_identity(directory)
    log("section", f"Installing {app} {version} as a private app")
    env = acs_env()
    acs(env, "apps", "install", "private", "--acs-legal-ack", "Y", "--app-package", str(package), main=True)

def listed_apps(env, splunkbase=False):
    apps, offset = [], 0
    while True:
        args = ["apps", "list", "--count", "100", "--offset", str(offset)]
        if splunkbase:
            args.append("--splunkbase=true")
        raw = acs(env, *args, "-f", "structured")
        try:
            rows = json.loads(raw)["apps"]
            if not isinstance(rows, list) or any(
                not isinstance(item, dict) or not isinstance(item.get("name"), str)
                for item in rows
            ):
                raise ValueError
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            log("error", "Missing apps in ACS output")
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
        env = acs_env()
        if custom:
            installed = listed_apps(env)
            splunkbase = {app.casefold() for app in listed_apps(env, True)}
            apps = sorted({app for app in installed if app.casefold() not in splunkbase})
        for app in apps:
            apps_file.write_text(json.dumps({"Apps": [app]}))
            try:
                acs(env, "apps", "export", f"--file={apps_file}", "--default=true", "--local=true",
                    "--users=true", "--confs-only=false", f"--export-dir={out}", main=True)
            except subprocess.CalledProcessError as error:
                if "APP_NOT_FOUND" not in f"{error.stdout}{error.stderr}":
                    raise
            exported = out / f"{app}.tar.gz"
            if exported.exists():
                exported.rename(out / f"{app}.tgz")
            else:
                log("warning", f"NOT INSTALLED {app}")
    finally:
        apps_file.unlink(missing_ok=True)

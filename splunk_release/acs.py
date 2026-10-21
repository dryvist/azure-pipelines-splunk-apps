"""Configure and operate the Splunk Cloud ACS CLI."""

import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
from pathlib import Path

from splunk_release.azure import http, log, run
from splunk_release.version import APP, TEXT, bumped, feed_versions, highest, set_version

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

# ACS returns these while another deployment task runs on the stack.
BUSY = ("424-failed-dependency", "503-service-unavailable")

def acs(env, *args, main=False):
    """Run an ACS CLI command and return stdout; output is grouped unless main or failed.

    A busy stack is retried every 30 seconds for up to 15 minutes."""
    if not main:
        log("group", f"acs {' '.join(args)}")
    deadline = time.monotonic() + 15 * 60
    result = run(["acs", *args], capture_output=True, text=True, env=env)
    while (result.returncode and any(code in f"{result.stdout}{result.stderr}" for code in BUSY)
           and time.monotonic() < deadline):
        log("warning", "ACS is busy with another deployment task, retrying in 30 seconds")
        time.sleep(30)
        result = run(["acs", *args], capture_output=True, text=True, env=env)
    if not main and result.returncode:
        log("endgroup")
    for output in (result.stdout, result.stderr):
        if output.strip():
            print(readable(output))
    if not main and not result.returncode:
        log("endgroup")
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result.stdout

def readable(output):
    """Output with each "response" JSON string of ACS structured output decoded, or the output unchanged."""
    try:
        items = json.loads(output)
        for item in items:
            item["response"] = json.loads(item["response"])
        return json.dumps(items, indent=2)
    except (ValueError, TypeError, KeyError):
        return output.rstrip()

def acs_env():
    """Environment whose HOME holds the ACS CLI configuration written by install-acs."""
    home = str(Path(os.environ["AGENT_TEMPDIRECTORY"]) / "acs-home")
    return {**os.environ, "HOME": home, "USERPROFILE": home}

def structured_response(env, *args):
    """Run an acs command with -f structured and return the decoded "response" object it prints."""
    try:
        response = json.loads(json.loads(acs(env, *args, "-f", "structured"))[0]["response"])
        if not isinstance(response, dict):
            raise ValueError("response must be an object")
        return response
    except (ValueError, IndexError, KeyError, TypeError):
        log("error", f'acs {" ".join(args)} output has no JSON "response" object')
        raise SystemExit(1)

def stack_status(env):
    return structured_response(env, "status", "current-stack")

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
    deadline = time.monotonic() + 15 * 60
    env = acs_env()
    while time.monotonic() < deadline:
        if version in acs(env, "apps", "describe", app):
            return
        time.sleep(min(15, max(0, deadline - time.monotonic())))
    log("error", f"Timed out after 15 minutes waiting for {app} version {version}")
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

def uninstall(directory):
    """Uninstall the package's app from the stack, or report that it is not installed."""
    _, app, _ = package_identity(directory)
    env, stack = acs_env(), os.environ["SPLUNK_STACK"]
    if app not in listed_apps(env):
        log("section", f"{app} is not installed on {stack}, nothing to uninstall")
        return
    log("warning", f"DANGER: uninstalling {app} from {stack} PERMANENTLY DELETES ALL of its lookups (CSV files)"
                   " and local settings")
    log("section", f"Uninstalling {app} from {stack}")
    acs(env, "apps", "uninstall", app, main=True)

def listed_apps(env, splunkbase=False):
    apps, offset = [], 0
    while True:
        args = ["apps", "list", "--count", "100", "--offset", str(offset)]
        if splunkbase:
            args.append("--splunkbase=true")
        rows = structured_response(env, *args).get("apps")
        if not isinstance(rows, list) or any(not isinstance(item, dict) or not isinstance(item.get("name"), str)
                                             for item in rows):
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

def stanza_names(stanzas):
    names = [name.strip() for name in stanzas.split(";") if name.strip()]
    if not names:
        sys.exit("No stanza names given; separate several with ;")
    return names

def rest(app, conf, stanza, method="GET"):
    """Call the search head REST API for one stanza in the app; return the body, or None when it does not exist."""
    base = configured_value("SPLUNK_REST_URL")
    if not base and configured_value("SPLUNK_SEARCH_HEAD"):
        sys.exit("SPLUNK_SEARCH_HEAD is set, so set SPLUNK_REST_URL to that search head's https://<host>:8089 URL")
    base = base or f"https://{os.environ['SPLUNK_STACK']}.splunkcloud.com:8089"
    app, conf, stanza = (urllib.parse.quote(value, safe="") for value in (app, conf, stanza))
    return http(f"{base.rstrip('/')}/servicesNS/nobody/{app}/configs/conf-{conf}/{stanza}?output_mode=json",
                {"Authorization": f"Bearer {os.environ['STACK_TOKEN']}"}, timeout=60, method=method, missing_ok=True)

def repackage(package, out_dir, app, version, conf=None, stanzas=()):
    """Write <out_dir>/<app>-<version>.tar.gz from package with a new version and without the given stanzas."""
    from ksconf.conf.parser import write_conf

    from splunk_release.compare import parse
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(package) as archive:
            archive.extractall(tmp, filter="data")
        root = Path(tmp, app)
        if stanzas:
            path = root / "default" / f"{conf}.conf"
            parsed = parse(path)
            missing = [name for name in stanzas if name not in parsed]
            if missing:
                sys.exit(f"default/{conf}.conf in {app} has no stanza [{'], ['.join(missing)}]; nothing to repair")
            write_conf(path, {name: keys for name, keys in parsed.items() if name not in stanzas})
        app_conf = root / "default" / "app.conf"
        app_conf.write_text(set_version(app_conf.read_text(**TEXT), version), **TEXT)
        manifest = root / "app.manifest"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["info"]["id"]["version"] = version
            manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        with tarfile.open(Path(out_dir, f"{app}-{version}.tar.gz"), "w:gz") as archive:
            archive.add(root, arcname=app)

def repair_packages(package_dir, out_dir, conf, stanzas):
    """Check each stanza on the stack, then write temp/ (next version, stanzas removed) and real/ (the version after)."""
    package, app, _ = package_identity(package_dir)
    names = stanza_names(stanzas)
    for name in names:
        if rest(app, conf, name) is None:
            sys.exit(f"[{name}] is not in {conf}.conf of {app} on {os.environ['SPLUNK_STACK']}. If an earlier repair "
                     "deleted it, run the deploy pipeline to install the latest package")
    installed = structured_response(acs_env(), "apps", "describe", app).get("version")
    base = highest(*feed_versions(app.lower()), *([installed] if installed else []))
    temp, real = bumped(base, "patch"), bumped(bumped(base, "patch"), "patch")
    repackage(package, Path(out_dir, "temp"), app, temp, conf, names)
    repackage(package, Path(out_dir, "real"), app, real)
    log("section", f"{app}: installed {installed}, highest {base}; temporary {temp} without "
                   f"{len(names)} {conf}.conf stanzas, then {real} with them")
    print(f"##vso[task.setvariable variable=REPAIR_APP]{app.lower()}")
    print(f"##vso[task.setvariable variable=REPAIR_VERSION]{real}")

def delete_local(package_dir, conf, stanzas):
    """Delete each stanza's local copy over REST; the temporary package has no default copy."""
    _, app, _ = package_identity(package_dir)
    for name in stanza_names(stanzas):
        if rest(app, conf, name, "DELETE") is None:
            print(f"[{name}] has no local copy in {app}, nothing to delete")
        else:
            log("section", f"Deleted the local copy of [{name}] in {conf}.conf of {app}")

def repair_check(package_dir, conf, stanzas):
    """Fail when any stanza is missing on the stack or still has a local copy in the exported app."""
    from splunk_release.compare import extract, parse

    _, app, _ = package_identity(package_dir)
    names = stanza_names(stanzas)
    with tempfile.TemporaryDirectory() as tmp:
        export(tmp, package_dir)
        exported = Path(tmp, app, f"{app}.tgz")
        if not exported.exists():
            sys.exit(f"{app} is not installed")
        root = Path(tmp, "app")
        extract(exported, root)
        local = parse(root / "local" / f"{conf}.conf")
    failed = [f"[{name}] still has a local copy" for name in names if name in local]
    failed += [f"[{name}] is missing" for name in names if rest(app, conf, name) is None]
    if failed:
        sys.exit(f"{conf}.conf in {app}: {'; '.join(failed)}")
    log("section", f"{len(names)} {conf}.conf stanzas in {app} now come from default only")

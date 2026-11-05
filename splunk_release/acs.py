"""Configure and operate the Splunk Cloud ACS CLI."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
from datetime import datetime
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
    shutil.unpack_archive(archive, directory, **({"filter": "data"} if archive.suffix == ".gz" else {}))
    print(f"##vso[task.prependpath]{directory}", flush=True)
    os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ['PATH']}"
    env = acs_env()
    Path(env["HOME"]).mkdir(exist_ok=True)
    stack, search_head = os.environ["SPLUNK_STACK"], configured_value("SPLUNK_SEARCH_HEAD")
    log("section", f"ACS stack {stack}, search head {search_head or 'not set, so ACS uses the primary search head'}")
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
        return json.loads(json.loads(acs(env, *args, "-f", "structured"))[0]["response"])
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
    packages = sorted(Path(directory).glob("*.tar.gz"))
    if not packages:
        sys.exit(f"Expected at least one .tar.gz package in {directory}, found none")
    identities = []
    for package in packages:
        app, _, version = package.name.removesuffix(".tar.gz").rpartition("-")
        if not app or not version:
            sys.exit(f"Expected <app-id>-<version>.tar.gz package name, found {package.name}")
        identities.append((package, app, version))
    return identities

def stack_ready(env):
    """Return (ready, state): ready when acs status current-stack reports infrastructure status Ready."""
    stack = stack_status(env).get("infrastructure", {}).get("status", "")
    if stack.lower() == "failed":
        log("error", f"ACS reports stack status {stack}")
        raise SystemExit(1)
    return stack.lower() == "ready", f"stack {stack or 'unknown'}"

def installed_version(env, app):
    """The app version acs apps describe reports, or None when the app is not installed."""
    try:
        return structured_response(env, "apps", "describe", app).get("version")
    except subprocess.CalledProcessError as error:
        if missing(error):
            return None
        raise

def missing(error):
    """True when a failed acs command reports that the app is not installed."""
    return "code: 404" in f"{error.stdout}{error.stderr}" or "APP_NOT_FOUND" in f"{error.stdout}{error.stderr}"

def wait_done(env, done, what, minutes=15, every=15):
    """Wait up to minutes until the stack is ready and done() is true, checking every `every` seconds."""
    deadline = time.monotonic() + minutes * 60
    while time.monotonic() < deadline:
        try:
            ready, state = stack_ready(env)
            ready = ready and done()
        except subprocess.CalledProcessError as error:
            if "code: 401" not in f"{error.stdout}{error.stderr}":
                raise
            ready, state = False, "ACS returned 401 Unauthorized, as it does while the search head restarts"
        if ready:
            log("section", f"{stamp()} {what} ({state})", flush=True)
            return
        print(f"{stamp()} Waiting for {what}: {state}", flush=True)
        time.sleep(min(every, max(0, deadline - time.monotonic())))
    log("error", f"Timed out after {minutes} minutes waiting for {what}")
    raise SystemExit(1)

def wait_version(directory):
    packages = package_identity(directory)
    env = acs_env()

    def matches():
        results = []
        for _, app, version in packages:
            installed = installed_version(env, app)
            if installed != version:
                print(f"acs apps describe reports {app} version {installed or 'not installed'}, expected {version}")
            results.append(installed == version)
        return all(results)

    expected = ", ".join(f"{app} version {version}" for _, app, version in packages)
    wait_done(env, matches, f"{expected} installed")

def restart(always=""):
    """Restart the search head when ACS reports a restart is required, or every time with --always.

    After the request, wait 60 seconds for the restart to begin, then until the stack is Ready with no pending restart."""
    if always not in ("", "--always"):
        sys.exit(f"Expected an optional --always, got {always}")
    env, stack = acs_env(), os.environ["SPLUNK_STACK"]
    where = configured_value("SPLUNK_SEARCH_HEAD") or f"{stack} primary search head"
    if not always and not restart_required(stack_status(env)):
        log("section", f"No restart required on {where}, skipping restart")
        return
    acs(env, "restart", "current-stack", main=True)
    print(f"{stamp()} Waiting 60 seconds for the restart of {where} to begin", flush=True)
    time.sleep(60)
    wait_done(env, lambda: not restart_required(stack_status(env)), f"restart of {where}", 30)

def deploy(directory):
    packages = package_identity(directory)
    env, stack = acs_env(), os.environ["SPLUNK_STACK"]
    wait_done(env, lambda: True, f"{stack} ready for the install", every=5)
    for _, app, version in packages:
        log("section", f"Installing {app} {version} as a private app")
    acs(env, "apps", "bulk-install", "private", "--package-src-dir", str(directory), "--acs-legal-ack=Y", main=True)

def uninstall(directory):
    """Uninstall the apps from all search heads in one bulk command, then wait until ACS lists none of them."""
    packages = package_identity(directory)
    all_apps = [app for _, app, _ in packages]
    env, stack = acs_env(), os.environ["SPLUNK_STACK"]
    apps = [app for app in all_apps if installed_version(env, app) is not None]
    if not apps:
        log("section", f"{', '.join(all_apps)} not installed on {stack}, skipping uninstall")
        return
    for app in apps:
        log("warning", f"DANGER: uninstalling {app} from {stack} PERMANENTLY DELETES ALL of its lookups (CSV files)"
                       " and local settings")
    with tempfile.TemporaryDirectory() as tmp:
        apps_file = Path(tmp, "apps.json")
        apps_file.write_text(json.dumps({"apps": apps}), encoding="utf-8")
        wait_done(env, lambda: True, f"{stack} ready for the uninstall", every=5)
        acs(env, "apps", "bulk-uninstall", "--file", str(apps_file), main=True)
    remaining = list(apps)

    def gone():
        remaining[:] = [app for app in remaining if installed_version(env, app) is not None]
        return not remaining
    wait_done(env, gone, f"{', '.join(apps)} gone from {stack}", every=5)

def listed_apps(env, splunkbase=False):
    apps, offset = [], 0
    while True:
        args = ["apps", "list", "--count", "100", "--offset", str(offset)]
        if splunkbase:
            args.append("--splunkbase=true")
        rows = structured_response(env, *args)["apps"]
        apps.extend(item["name"] for item in rows)
        if len(rows) < 100:
            return apps
        offset += 100

def stamp():
    """The local time in ISO 8601 form, with a space in place of the T."""
    return datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")

def export_app(env, apps_file, out, default):
    """Run acs apps export for the app in apps_file; return the ACS output on failure, or "" on success."""
    try:
        acs(env, "apps", "export", f"--file={apps_file}", f"--default={default}", "--local=true",
            "--users=true", "--confs-only=false", f"--export-dir={out}", main=True)
        return ""
    except subprocess.CalledProcessError as error:
        return f"{error.stdout}{error.stderr}"

def export(out_dir, *app_ids):
    """Export each app to <out_dir>/<app>.tgz. --all exports every installed app.

    The built-in search app exports only its local and user files. An app ACS does not export is skipped with a
    warning, and the export fails only when no app exports."""
    package_dir = len(app_ids) == 1 and Path(app_ids[0]).is_dir()
    every = app_ids == ("--all",)
    out, apps = Path(out_dir), app_ids or [APP]
    if package_dir:
        _, app, _ = package_identity(app_ids[0])[0]
        apps = [app]
        out /= app
        print(f"##vso[task.setvariable variable=APP_ID]{app}")

    out.mkdir(parents=True, exist_ok=True)
    env = acs_env()
    if every:
        apps = sorted(set(listed_apps(env)) | set(listed_apps(env, True)))
    skipped, missing = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for number, app in enumerate(apps, 1):
            log("section", f"{stamp()} Export {number} of {len(apps)}: {app}", flush=True)
            # The file name puts the app name in the logged acs command.
            apps_file = Path(tmp, f"{app}.json")
            apps_file.write_text(json.dumps({"apps": [app]}))
            error = export_app(env, apps_file, out, "true")
            if "ONLY LOCAL AND USERS CONFIGS ALLOWED" in error:
                log("warning", f"{stamp()} LOCAL AND USERS ONLY {app}: ACS does not export its default files. "
                               "Exporting its local and user files", flush=True)
                error = export_app(env, apps_file, out, "false")
            exported = out / f"{app}.tar.gz"
            if error and "APP_NOT_FOUND" not in error:
                skipped.append(app)
                exported.unlink(missing_ok=True)
                log("warning", f"{stamp()} SKIPPED {app}: ACS did not export it. See the ACS output above", flush=True)
            elif exported.exists():
                print(f"{stamp()} EXPORTED {app}: {exported.stat().st_size:,} bytes", flush=True)
                exported.rename(out / f"{app}.tgz")
            else:
                missing.append(app)
                log("warning", f"{stamp()} NOT INSTALLED {app}", flush=True)
    print(f"{stamp()} Export result: {len(apps) - len(skipped) - len(missing)} exported, {len(skipped)} skipped, "
          f"{len(missing)} not installed, of {len(apps)} app(s)", flush=True)
    if skipped and len(skipped) == len(apps):
        log("error", f"ACS exported none of {len(apps)} app(s). Check the token and its export_apps capability")
        raise SystemExit(1)

def stanza_names(stanzas):
    names = [name.strip() for name in stanzas.split(";") if name.strip()]
    if not names:
        sys.exit("No stanza names given; separate several with ;")
    return names

def rest(app, conf, stanza, method="GET"):
    """Call the search head REST API for one stanza in the app; return the body, or None when it does not exist."""
    app, conf, stanza = (urllib.parse.quote(value, safe="") for value in (app, conf, stanza))
    host = ".".join(filter(None, (configured_value("SPLUNK_SEARCH_HEAD"), os.environ["SPLUNK_STACK"])))
    return http(f"https://{host}.splunkcloud.com:8089/servicesNS/nobody/{app}/configs/conf-{conf}/{stanza}?output_mode=json",
                {"Authorization": f"Bearer {os.environ['STACK_TOKEN']}"}, timeout=60, method=method, missing_ok=True)

def saved_searches(action, apps, searches, state_file, write=""):
    """Plan, or with --write apply, action (disable or enable) on each app's shared scheduled searches.

    apps and searches are names separated by ;, and searches can be all. Private searches are left alone. A rerun
    skips searches that are already done. state_file gets each search's disabled state before the run."""
    import splunklib.client as client

    if action not in ("disable", "enable") or write not in ("", "--write"):
        sys.exit(f"Expected disable or enable and an optional --write, got {action} {write}".rstrip())
    wanted = None if searches.strip().lower() in ("", "all") else set(stanza_names(searches))
    host = ".".join(filter(None, (configured_value("SPLUNK_SEARCH_HEAD"), os.environ["SPLUNK_STACK"])))
    states, changed = [], 0
    for app in stanza_names(apps.replace(" ", ";")):
        service = client.connect(host=f"{host}.splunkcloud.com", port=8089, splunkToken=os.environ["STACK_TOKEN"],
                                 owner="nobody", app=app)
        found = [s for s in service.saved_searches.list() if s.access.app == app and s.access.sharing != "user"
                 and s["is_scheduled"] == "1" and (wanted is None or s.name in wanted)]
        log("section", f"{stamp()} {app}: {len(found)} shared scheduled search(es)", flush=True)
        for search in found:
            disabled = search["disabled"] == "1"
            states.append({"app": app, "search": search.name, "disabled": disabled})
            if disabled == (action == "disable"):
                print(f"{stamp()} ALREADY {action.upper()}D {app}/{search.name}", flush=True)
                continue
            changed += 1
            if write:
                getattr(search, action)()
            print(f"{stamp()} {action.upper()}{'D' if write else ''} {app}/{search.name}", flush=True)
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    Path(state_file).write_text(json.dumps(states, indent=1), encoding="utf-8")
    print(f"{stamp()} Result: {changed} {action}d" if write else f"{stamp()} Result: {changed} to {action}",
          f"of {len(states)} shared scheduled search(es)", flush=True)

def require_private(app):
    """Exit unless ACS lists the app as installed and not from Splunkbase."""
    env = acs_env()
    if app.casefold() in {name.casefold() for name in listed_apps(env, True)}:
        sys.exit(f"{app} is a Splunkbase app. Onboard takes private apps only")
    if app not in listed_apps(env):
        sys.exit(f"{app} is not installed on this search head. App IDs are case-sensitive")
    print(f"{app} is installed and not from Splunkbase")

def repackage(package, out_dir, app, version, conf=None, stanzas=()):
    """Write <out_dir>/<app>-<version>.tar.gz from package with a new version and without the given stanzas."""
    from ksconf.conf.parser import write_conf

    from splunk_release.compare import extract, parse
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp, app)
        extract(package, root)
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
    package, app, _ = package_identity(package_dir)[0]
    names = stanza_names(stanzas)
    for name in names:
        if rest(app, conf, name) is None:
            sys.exit(f"[{name}] is not in {conf}.conf of {app} on {os.environ['SPLUNK_STACK']}. If an earlier repair "
                     "deleted it, run the deploy pipeline to install the latest package")
    installed = installed_version(acs_env(), app)
    base = highest(*feed_versions(app.lower()), *([installed] if installed else []))
    temp, real = bumped(base, "patch"), bumped(bumped(base, "patch"), "patch")
    repackage(package, Path(out_dir, "temp"), app, temp, conf, names)
    repackage(package, Path(out_dir, "real"), app, real)
    log("section", f"{app}: installed {installed}, highest {base}; temporary {temp} without "
                   f"{len(names)} {conf}.conf stanzas, then {real} with them")
    print(f"##vso[task.setvariable variable=REPAIR_VERSION]{real}")

def delete_local(package_dir, conf, stanzas):
    """Delete each stanza's local copy over REST; the temporary package has no default copy."""
    _, app, _ = package_identity(package_dir)[0]
    for name in stanza_names(stanzas):
        if rest(app, conf, name, "DELETE") is None:
            print(f"[{name}] has no local copy in {app}, nothing to delete")
        else:
            log("section", f"Deleted the local copy of [{name}] in {conf}.conf of {app}")

def repair_check(package_dir, conf, stanzas):
    """Fail when any stanza is missing on the stack or still has a local copy in the exported app."""
    from splunk_release.compare import extract, parse

    _, app, _ = package_identity(package_dir)[0]
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

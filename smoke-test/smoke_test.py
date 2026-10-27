#!/usr/bin/env python3
"""Check AppInspect login and Splunk Cloud ACS access."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from splunk_release.acs import (
    acs_env, configured_value, installed_version, listed_apps, rest, restart_required, stack_ready, stack_status,
)
from splunk_release.appinspect import appinspect_token
from splunk_release.azure import print_colored_patch, run, run_cli


def require(group, *names):
    """Stop with one clear line when a variable group value is missing."""
    missing = [n for n in names if configured_value(n) is None]
    if missing:
        sys.exit(f"FAIL {group}: empty value for {', '.join(missing)}")


def appinspect():
    require("splunk-appinspect", "SPLUNK_USERNAME", "SPLUNK_PASSWORD")
    appinspect_token()
    print_colored_patch("PASS AppInspect login")


def stack(group):
    """List apps and export the built-in search app's local and user files with the ACS CLI."""
    names = ["SPLUNK_STACK", "ACS_TOKEN"]
    if group.startswith("splunk-itsi-"):
        names.append("SPLUNK_SEARCH_HEAD")
    require(group, *names)
    os.environ["STACK_TOKEN"] = os.environ["ACS_TOKEN"]
    env = acs_env()
    with tempfile.TemporaryDirectory() as out:
        run(["acs", "apps", "list"], check=True, env=env, capture_output=True)
        print_colored_patch(f"PASS {group} ACS login and app list")
        apps_file = Path(out, "apps.json")
        apps_file.write_text(json.dumps({"Apps": ["search"]}))
        cmd = ["acs", "apps", "export", f"--file={apps_file}", "--default=false", "--local=true",
               "--users=true", "--confs-only=true", f"--export-dir={out}"]
        print("Exporting the search app local and user configuration files only.")
        run(cmd, check=True, env=env)
        print_colored_patch(f"PASS {group} export_apps: {Path(out, 'search.tar.gz').stat().st_size} bytes")
    stack_reads(group, env)


def stack_reads(group, env):
    """Read stack status, app listings, the search app version and the search head REST API."""
    _, state = stack_ready(env)
    restart = "yes" if restart_required(stack_status(env)) else "no"
    print_colored_patch(f"PASS {group} {state}, restart required: {restart}")
    installed = listed_apps(env)
    splunkbase = listed_apps(env, True)
    print_colored_patch(f"PASS {group} app listings: {len(installed)} apps, {len(splunkbase)} from Splunkbase")
    version = installed_version(env, "search")
    if version is None:
        sys.exit(f"FAIL {group}: search app is not installed")
    print_colored_patch(f"PASS {group} apps describe search: version {version}")
    launcher = rest("search", "app", "launcher")
    found = "found" if launcher is not None else "not found"
    print_colored_patch(f"PASS {group} search head REST: token accepted, launcher stanza {found}")


def result(*results):
    """Print each job result and fail unless all succeeded."""
    for name, value in zip(("appinspect", "nonprod", "prod"), results):
        print(f"{name}: {value}")
    if set(results) == {"Succeeded"}:
        print_colored_patch("RESULT: ALL PASS")
    else:
        print_colored_patch("RESULT: FAILED - open each failed job for its FAIL or Error line")
        sys.exit(1)


def dispatch(name, *args):
    if name == "result":
        result(*args)
    elif name == "appinspect":
        appinspect()
    else:
        stack(name)


if __name__ == "__main__":
    name, *args = sys.argv[1:] or ["help"]
    run_cli(dispatch, name, *args)

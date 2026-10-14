#!/usr/bin/env python3
"""Check AppInspect login and Splunk Cloud ACS access."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from splunk_release.acs import acs_env, configured_value
from splunk_release.appinspect import appinspect_token
from splunk_release.azure import report_command_error, run


def require(group, *names):
    """Stop with one clear line when a variable group value is missing."""
    missing = [n for n in names if configured_value(n) is None]
    if missing:
        sys.exit(f"FAIL {group}: empty value for {', '.join(missing)}")


def appinspect():
    require("splunk-appinspect", "SPLUNK_USERNAME", "SPLUNK_PASSWORD")
    appinspect_token()
    print("PASS AppInspect login")


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
        print(f"PASS {group} ACS login and app list")
        apps_file = Path(out, "apps.json")
        apps_file.write_text(json.dumps({"Apps": ["search"]}))
        cmd = ["acs", "apps", "export", f"--file={apps_file}", "--default=false", "--local=true",
               "--users=true", "--confs-only=true", f"--export-dir={out}"]
        print("Exporting the search app local and user configuration files only.")
        run(cmd, check=True, env=env)
        print(f"PASS {group} export_apps: {Path(out, 'search.tar.gz').stat().st_size} bytes")


def result(*results):
    """Print each job result and fail unless all succeeded."""
    for name, value in zip(("appinspect", "nonprod", "prod"), results):
        print(f"{name}: {value}")
    if set(results) == {"Succeeded"}:
        print("RESULT: ALL PASS")
    else:
        print("RESULT: FAILED - open each failed job for its FAIL or Error line")
        sys.exit(1)


if __name__ == "__main__":
    command, *args = sys.argv[1:] or ["help"]
    try:
        if command == "result":
            result(*args)
        elif command == "appinspect":
            appinspect()
        else:
            stack(command)
    except subprocess.CalledProcessError as error:
        report_command_error(error)
        sys.exit(error.returncode)

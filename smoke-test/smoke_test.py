#!/usr/bin/env python3
"""Check AppInspect login and Splunk Cloud ACS access."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release


def require(group, *names):
    """Stop with one clear line when a variable group value is missing."""
    missing = [n for n in names if not os.environ.get(n, "").strip() or os.environ[n].startswith("$(")]
    if missing:
        sys.exit(f"FAIL {group}: empty value for {', '.join(missing)}")


def appinspect():
    require("splunk-appinspect", "SPLUNK_USERNAME", "SPLUNK_PASSWORD")
    release.appinspect_token()
    print("PASS AppInspect login")


def stack(group):
    """List apps and export the built-in search app's local and user files with the ACS CLI."""
    require(group, "SPLUNK_STACK", "ACS_TOKEN")
    os.environ["STACK_TOKEN"] = os.environ["ACS_TOKEN"]
    with tempfile.TemporaryDirectory() as out, release.acs_session() as env:
        subprocess.run(["acs", "apps", "list"], check=True, env=env, capture_output=True)
        print(f"PASS {group} ACS login and app list")
        Path(out, "apps.json").write_text(json.dumps({"Apps": ["search"]}))
        cmd = ["acs", "apps", "export", f"--file={out}/apps.json", "--default=false", "--local=true",
               "--users=true", "--confs-only=true", f"--export-dir={out}"]
        subprocess.run(cmd, check=True, env=env)
        print(f"PASS {group} export_apps: {Path(out, 'search.tgz').stat().st_size} bytes")


checks = {
    "appinspect": appinspect,
    "nonprod": lambda: stack("splunk-nonprod"),
    "prod": lambda: stack("splunk-prod"),
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in checks:
        sys.exit("Usage: python smoke-test/smoke_test.py <appinspect|nonprod|prod>")
    checks[sys.argv[1]]()

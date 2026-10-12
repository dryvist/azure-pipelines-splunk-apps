#!/usr/bin/env python3
"""Check AppInspect login and Splunk Cloud ACS access."""

import json
import os
import sys
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


def acs_apps():
    url = (
        f"https://admin.splunk.com/{os.environ['SPLUNK_STACK']}"
        "/adminconfig/v2/apps/victoria"
    )
    data = release.http(
        url,
        {"Authorization": f"Bearer {os.environ['ACS_TOKEN']}"},
    )
    return len(json.loads(data)["apps"])


def nonprod():
    require("splunk-nonprod", "SPLUNK_STACK", "ACS_TOKEN")
    print(f"PASS nonprod ACS: {acs_apps()} apps")


def prod():
    require("splunk-prod", "SPLUNK_STACK", "ACS_TOKEN")
    print(f"PASS prod ACS: {acs_apps()} apps")
    url = (
        f"https://admin.splunk.com/{os.environ['SPLUNK_STACK']}"
        "/adminconfig/v2/apps/victoria/export/download/search"
        "?default=false&local=true&users=true"
    )
    body = release.http(url, {"Authorization": f"Bearer {os.environ['ACS_TOKEN']}"})
    print(f"PASS prod export_apps: {len(body)} bytes")


checks = {
    "appinspect": appinspect,
    "nonprod": nonprod,
    "prod": prod,
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in checks:
        sys.exit("Usage: python smoke-test/smoke_test.py <appinspect|nonprod|prod>")
    checks[sys.argv[1]]()

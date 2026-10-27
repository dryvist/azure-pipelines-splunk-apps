#!/usr/bin/env python3
"""Check AppInspect login, Splunk Cloud ACS access and Azure DevOps rights."""

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
from splunk_release.azure import http, print_colored_patch, run, run_cli
from splunk_release.import_app import ONBOARD_RESOURCES
from splunk_release.version import feed_versions


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
    """Read stack status, app listings and the search app version."""
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


def search_head_rest(group):
    """Read the search app's launcher stanza over the search head REST API on port 8089."""
    os.environ["STACK_TOKEN"] = os.environ["ACS_TOKEN"]
    try:
        launcher = rest("search", "app", "launcher")
    except SystemExit as error:
        try:
            ip = http("https://api.ipify.org", {}, timeout=10).decode().strip()
        except SystemExit:
            ip = "unknown: https://api.ipify.org is not reachable"
        # A warning keeps the job green: only Repair needs port 8089.
        print(f"##vso[task.logissue type=warning]WARN {group} port 8089: {error.code}. Agent public IP: {ip}. "
              "Add it as <ip>/32 to the search-api IP allow list. Only Repair needs port 8089")
        return
    found = "found" if launcher is not None else "not found"
    print_colored_patch(f"PASS {group} port 8089 search head REST: token accepted, launcher stanza {found}")


def azure_devops():
    """Check the job token can read the onboard resources and the splunk-apps feed, and has the repository rights."""
    require("azure-devops", "SYSTEM_ACCESSTOKEN", "SYSTEM_COLLECTIONURI", "SYSTEM_TEAMPROJECTID", "BUILD_REPOSITORY_ID")
    headers = {"Authorization": f"Bearer {os.environ['SYSTEM_ACCESSTOKEN']}"}
    collection = os.environ["SYSTEM_COLLECTIONURI"].rstrip("/") + "/"
    project_id = os.environ["SYSTEM_TEAMPROJECTID"]
    for resource_type, query in ONBOARD_RESOURCES:
        name = query.split("=", 1)[1]
        found = json.loads(http(f"{collection}{project_id}/_apis/distributedtask/{query}&api-version=7.1", headers))
        if not found["value"]:
            sys.exit(f"FAIL azure-devops: {resource_type} {name} not found")
        print_colored_patch(f"PASS azure-devops: {resource_type} {name} found")
    feed_versions("smoke-test")
    print_colored_patch("PASS azure-devops: splunk-apps feed read")
    git_repositories = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
    rights = (
        ("Create repository", 256, f"repoV2/{project_id}"),
        ("Contribute to pull requests", 16384, f"repoV2/{project_id}/{os.environ['BUILD_REPOSITORY_ID']}"),
    )
    for label, bit, token in rights:
        url = f"{collection}_apis/permissions/{git_repositories}/{bit}?tokens={token}&api-version=7.1"
        if json.loads(http(url, headers))["value"] != [True]:
            sys.exit(f"FAIL azure-devops: Build Service lacks {label}")
        print_colored_patch(f"PASS azure-devops: Build Service has {label}")


def result():
    """Print each RESULT_<job> variable and fail unless all succeeded."""
    results = {name[7:].lower(): value for name, value in sorted(os.environ.items()) if name.upper().startswith("RESULT_")}
    for name, value in results.items():
        print(f"{name}: {value}")
    if set(results.values()) == {"Succeeded"}:
        print_colored_patch("RESULT: ALL PASS")
    else:
        print_colored_patch("RESULT: FAILED - open each failed job for its FAIL or Error line")
        sys.exit(1)


def dispatch(name, *args):
    if name == "result":
        result()
    elif name == "appinspect":
        appinspect()
    elif name == "azuredevops":
        azure_devops()
    elif name == "rest":
        search_head_rest(*args)
    else:
        stack(name)


if __name__ == "__main__":
    name, *args = sys.argv[1:] or ["help"]
    run_cli(dispatch, name, *args)

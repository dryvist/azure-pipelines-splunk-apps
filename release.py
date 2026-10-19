#!/usr/bin/env python3
"""Release, compare, and tag the Splunk app stored in ./package.

release.py bump                         update app.conf and app.manifest, then push the PR version (CI only)
release.py package                      stage package/ and write dist/<app-id>-<version>.tar.gz
release.py appinspect <dir>             submit the package in <dir> to AppInspect
release.py deploy <dir>                 install the single .tar.gz in <dir> with the ACS CLI
release.py status                       report current-stack status and pending restart
release.py wait-version <dir>           wait until ACS reports the packaged app version
release.py restart                      restart current-stack only when a restart is required, then wait
release.py export <out-dir> [app-id...] export app data, custom apps (--custom), or a package directory
release.py tree <target> <source> <out> compare raw files and write tree reports
release.py local-diff <target> <source> <out> compare target local files with the same source default stanzas
release.py diff <target> <source> <out> merge local into default on both sides, compare, write artifacts
release.py install-acs                  download and verify the ACS CLI, add it to PATH, add the stack, log in
release.py appinspect-link              print the link to this build's published artifacts
release.py plan                         print which stages this run executes and why
release.py tag                          tag HEAD as v<version>, push the tag, and set APP_ID/APP_VERSION (CI only)
release.py import-nonprod <export-dir>  replace package/ from a nonprod export and open a pull request

The ACS CLI reads STACK_TOKEN. Azure Pipelines maps ACS_TOKEN to STACK_TOKEN.
SPLUNK_SEARCH_HEAD selects a target search head for compare and smoke tests.
"""

import subprocess
import sys

from splunk_release.acs import deploy, export, install_acs, restart, status, wait_version
from splunk_release.appinspect import appinspect
from splunk_release.azure import appinspect_link, plan, report_command_error
from splunk_release.compare import diff, local_diff, tree
from splunk_release.import_nonprod import import_nonprod
from splunk_release.package import package
from splunk_release.version import bump, tag

commands = {
    "bump": bump,
    "package": package,
    "appinspect": appinspect,
    "deploy": deploy,
    "status": status,
    "wait-version": wait_version,
    "restart": restart,
    "plan": plan,
    "export": export,
    "tree": tree,
    "local-diff": local_diff,
    "diff": diff,
    "install-acs": install_acs,
    "appinspect-link": appinspect_link,
    "tag": tag,
    "import-nonprod": import_nonprod,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except subprocess.CalledProcessError as error:
        report_command_error(error)
        sys.exit(error.returncode)

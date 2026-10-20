#!/usr/bin/env python3
"""Release, compare, and tag the Splunk app stored in ./package.

release.py bump                         update app.conf and app.manifest, then push the PR version (CI only)
release.py package                      stage package/ and write dist/<app-id>-<version>.tar.gz
release.py appinspect <dir>             submit the package in <dir> to AppInspect
release.py deploy <dir>                 install the single .tar.gz in <dir> with the ACS CLI
release.py status                       report current-stack status and pending restart
release.py uninstall <dir>              uninstall the app in <dir> from the stack when it is installed
release.py wait-version <dir>           wait until ACS reports the packaged app version
release.py restart                      restart current-stack only when a restart is required, then wait
release.py export <out-dir> [app-id...] export app data, custom apps (--custom), or a package directory
release.py tree <target> <source> <out> [--reverse] [--skip-lookups] compare raw files and write tree reports
release.py local-diff <target> <source> <out> [--reverse] [--skip-lookups] compare target local files with the same source default stanzas
release.py diff <target> <source> <out> [--reverse] [--skip-lookups] merge local into default on both sides, compare, write artifacts
release.py data-models <target> <source> <out> [--reverse] [--skip-lookups] compare data model JSON after merging local
release.py install-acs                  download and verify the ACS CLI, add it to PATH, add the stack, log in
release.py appinspect-link              print the link to this build's published artifacts
release.py plan                         print which stages this run executes and why
release.py feed-check <app-id>          fail when the splunk-apps feed holds no version of the app
release.py tag                          tag HEAD as v<version>, push the tag, and set APP_ID/APP_VERSION (CI only)
release.py import-nonprod <export-dir> [--skip-lookups] [--skip-lookup-backups] replace package/ from a nonprod export and open a pull request
release.py repair-packages <dir> <out-dir> <conf> <stanzas> write <out-dir>/temp without the stanzas and <out-dir>/real
release.py delete-local <dir> <conf> <stanzas>   delete each stanza's local copy over the search head REST API
release.py repair-check <dir> <conf> <stanzas>   fail when a stanza is missing or still has a local copy

The ACS CLI reads STACK_TOKEN. Azure Pipelines maps ACS_TOKEN to STACK_TOKEN.
--reverse shows source lines as - and target lines as +. --skip-lookups ignores lookups/ on both sides
and, for import-nonprod, keeps the lookups already in package/. --skip-lookup-backups ignores
lookups/lookup_file_backups/. <stanzas> are separated by ;. SPLUNK_REST_URL sets the REST API URL.
SPLUNK_SEARCH_HEAD selects a target search head for compare and smoke tests.
"""

import subprocess
import sys

from splunk_release.acs import (delete_local, deploy, export, install_acs, repair_check, repair_packages, restart,
                                status, uninstall, wait_version)
from splunk_release.appinspect import appinspect
from splunk_release.azure import appinspect_link, plan, report_command_error, report_system_exit
from splunk_release.compare import data_models, diff, local_diff, tree
from splunk_release.import_nonprod import import_nonprod
from splunk_release.package import package
from splunk_release.version import bump, feed_check, tag

commands = {
    "bump": bump,
    "package": package,
    "appinspect": appinspect,
    "deploy": deploy,
    "uninstall": uninstall,
    "status": status,
    "wait-version": wait_version,
    "restart": restart,
    "plan": plan,
    "export": export,
    "tree": tree,
    "local-diff": local_diff,
    "diff": diff,
    "data-models": data_models,
    "install-acs": install_acs,
    "appinspect-link": appinspect_link,
    "feed-check": feed_check,
    "tag": tag,
    "import-nonprod": import_nonprod,
    "repair-packages": repair_packages,
    "delete-local": delete_local,
    "repair-check": repair_check,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except subprocess.CalledProcessError as error:
        report_command_error(error)
        sys.exit(error.returncode)
    except SystemExit as error:
        report_system_exit(error)
        raise

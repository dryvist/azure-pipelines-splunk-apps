#!/usr/bin/env python3
"""release.py commands:
  bump
  package
  acs <args...>
  appinspect <dir>
  deploy <dir>
  uninstall <dir>
  status
  wait-version <dir>
  restart
  plan
  export <out-dir> [app-id...]
  tree <target> <source> <out> [flags]
  local-diff <target> <source> <out> [flags]
  diff <target> <source> <out> [flags]
  data-models <target> <source> <out> [flags]
  install-acs
  appinspect-link
  feed-check <app-id>
  stages-succeeded <stage...>
  feed-missing <app-id>
  tag
  import <env> <export-dir> [flags]
  onboard <app>
  repair-packages <dir> <out-dir> <conf> <stanzas>
  delete-local <dir> <conf> <stanzas>
  repair-check <dir> <conf> <stanzas>
"""

import sys

from splunk_release.acs import (
    acs, acs_env, delete_local, deploy, export, install_acs, repair_check,
    repair_packages, restart, status, uninstall, wait_version,
)
from splunk_release.appinspect import appinspect
from splunk_release.azure import appinspect_link, plan, run_cli, stages_succeeded
from splunk_release.compare import data_models, diff, local_diff, tree
from splunk_release.import_app import import_app, onboard
from splunk_release.package import package
from splunk_release.version import bump, feed_check, feed_missing, tag


def acs_command(*args):
    acs(acs_env(), *args, main=True)


commands = {
    "bump": bump,
    "package": package,
    "acs": acs_command,
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
    "stages-succeeded": stages_succeeded,
    "feed-missing": feed_missing,
    "tag": tag,
    "import": import_app,
    "onboard": onboard,
    "repair-packages": repair_packages,
    "delete-local": delete_local,
    "repair-check": repair_check,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    run_cli(commands[sys.argv[1]], *sys.argv[2:])

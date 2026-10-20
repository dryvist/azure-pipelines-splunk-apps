"""Import the nonprod app into a new app repository branch and pull request."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from splunk_release import compare
from splunk_release.azure import http, log
from splunk_release.package import sort_confs
from splunk_release.version import (
    APP,
    CONF,
    SRC,
    TEXT,
    app_conf_version,
    bumped,
    generate_manifest,
    git,
    set_version,
)


# Settings Splunk Cloud AppInspect rejects: the value an import writes, or None to remove the setting.
CLOUD_OFF = {"datamodels.conf": ("acceleration", "false"), "savedsearches.conf": ("action.populate_lookup", None)}


def cloud_settings_off(root):
    """Turn off or remove settings in default/ that Splunk Cloud AppInspect rejects, with one warning each."""
    from ksconf.conf.parser import write_conf
    for name, (key, off) in CLOUD_OFF.items():
        path = root / "default" / name
        conf = compare.parse(path)
        changed = [s for s, keys in conf.items()
                   if key in keys and (off is None or keys[key].strip().lower() not in ("0", "f", "false", "n", "no", "off"))]
        for stanza in changed:
            if off is None:
                del conf[stanza][key]
            else:
                conf[stanza][key] = off
            log("warning", f"default/{name} [{stanza}] {key} {'removed' if off is None else '= ' + off}: not allowed in Splunk Cloud apps")
        if changed:
            write_conf(path, conf)


def open_pull_request(branch, version):
    """Push an import branch and create its pull request into main."""
    build_id = os.environ["BUILD_BUILDID"]
    source = f"refs/heads/{branch}"
    url = (
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECTID']}"
        f"/_apis/git/repositories/{os.environ['BUILD_REPOSITORY_ID']}/pullrequests"
        "?api-version=7.1"
    )
    body = {
        "sourceRefName": source,
        "targetRefName": "refs/heads/main",
        "title": f"Import {APP} {version} from nonprod",
        "description": f"Created by build {build_id}.",
    }
    response = json.loads(
        http(
            url,
            {
                "Authorization": f"Bearer {os.environ['SYSTEM_ACCESSTOKEN']}",
                "Content-Type": "application/json",
            },
            json.dumps(body).encode("utf-8"),
        )
    )
    pull_request_url = (
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECT']}"
        f"/_git/{os.environ['BUILD_REPOSITORY_NAME']}/pullrequest/"
        f"{response['pullRequestId']}"
    )
    print(pull_request_url)


def import_nonprod(export_dir, *flags):
    """Replace package/ with the merged nonprod export and open a pull request."""
    if set(flags) - set(compare.SKIPPED):
        sys.exit(f"Unknown option: {' '.join(flags)}")
    version = bumped(app_conf_version(CONF.read_text(**TEXT)), "patch")
    archive = Path(export_dir, f"{APP}.tgz")
    if not archive.is_file():
        sys.exit(f"Nonprod export is missing {archive.name}; confirm the app is installed")

    with tempfile.TemporaryDirectory() as temp_dir:
        imported = Path(temp_dir, APP)
        compare.extract(archive, imported)
        compare.merge_local(imported)
        for path in compare.files(imported):
            if compare.kept(path):
                (imported / path).unlink()
        cloud_settings_off(imported)
        for flag, folder in compare.SKIPPED.items():
            if flag in flags:
                shutil.rmtree(imported / folder, ignore_errors=True)
        if "--skip-lookups" in flags and (SRC / "lookups").is_dir():
            # Keep the lookups already on main.
            shutil.copytree(SRC / "lookups", imported / "lookups")
        imported_conf = imported / "default" / "app.conf"
        imported_conf.write_text(
            set_version(imported_conf.read_text(**TEXT), version), **TEXT
        )
        shutil.rmtree(SRC)
        shutil.copytree(imported, SRC)

    sort_confs(SRC)
    generate_manifest()
    build_id = os.environ["BUILD_BUILDID"]
    branch = f"nonprod-import/{version}-{build_id}"
    git("checkout", "-b", branch)
    git("add", "--all", str(SRC))
    git("commit", "-m", f"Import {APP} {version} from nonprod")
    git("push", "origin", f"HEAD:refs/heads/{branch}")
    open_pull_request(branch, version)

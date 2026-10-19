"""Import the nonprod app into a new app repository branch and pull request."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from splunk_release import compare
from splunk_release.azure import http
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


def import_nonprod(export_dir):
    """Replace package/ with the merged nonprod export and open a pull request."""
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

"""Tests for the nonprod import command."""

from unittest import TestCase

import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _common import CONF, write_tgz
from splunk_release import import_nonprod


def check_import_nonprod():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        package = root / "package"
        package.mkdir()
        (package / "default").mkdir()
        (package / "default" / "old.conf").write_text("[old]\nvalue = remove\n")
        (package / "lookups").mkdir()
        (package / "lookups" / "keep.csv").write_text("h\nmain\n")
        main_conf = package / "default" / "app.conf"
        main_conf.write_text(CONF, encoding="utf-8")
        export_dir = root / "nonprod-export"
        export_dir.mkdir()
        write_tgz(
            export_dir / "my_ta.tgz",
            {
                "my_ta/default/app.conf": CONF,
                "my_ta/default/props.conf": "[changed]\nvalue = default\n",
                "my_ta/local/props.conf": "[changed]\nvalue = local\n",
                "my_ta/lookups/keep.csv": "h\nnonprod\n",
                "my_ta/lookups/new.csv": "h\n1\n",
                "my_ta/default/datamodels.conf": "[Fast]\nacceleration = 0\n\n[Slow]\nacceleration = false\n",
                "my_ta/local/datamodels.conf": "[Fast]\nacceleration = 1\n",
                "my_ta/local/savedsearches.conf": "[fill]\naction.populate_lookup = 1\nsearch = x\n",
                "my_ta/local/data/ui/views/example.xml": "<view/>\n",
                "my_ta/metadata/local.meta": "[my_ta]\naccess = read : [*]\n",
                "my_ta/users/admin/local/savedsearches.conf": "[search]\n",
            },
        )
        manifest = package / "app.manifest"

        def write_manifest():
            manifest.write_text("generated manifest\n", encoding="utf-8")

        environment = {
            "BUILD_BUILDID": "8421",
            "BUILD_REPOSITORY_ID": "<repo-id>",
            "BUILD_REPOSITORY_NAME": "<app-id>",
            "SYSTEM_ACCESSTOKEN": "test-token",
            "SYSTEM_COLLECTIONURI": "https://dev.azure.com/<org>/",
            "SYSTEM_TEAMPROJECT": "<project>",
            "SYSTEM_TEAMPROJECTID": "<project-id>",
        }
        output = io.StringIO()
        with (
            patch("splunk_release.import_nonprod.SRC", package),
            patch("splunk_release.import_nonprod.CONF", main_conf),
            patch("splunk_release.import_nonprod.APP", "my_ta"),
            patch("splunk_release.import_nonprod.generate_manifest", side_effect=write_manifest) as generate,
            patch("splunk_release.import_nonprod.git") as git,
            patch("splunk_release.import_nonprod.http", return_value=b'{"pullRequestId": 34}') as http,
            patch.dict(os.environ, environment),
            redirect_stdout(output),
        ):
            import_nonprod.import_nonprod(export_dir, "--skip-lookups")

        version = "1.4.10"
        branch = f"nonprod-import/{version}-8421"
        generate.assert_called_once_with()
        assert git.call_args_list == [
            (("checkout", "-b", branch),),
            (("add", "--all", str(package)),),
            (("commit", "-m", f"Import my_ta {version} from nonprod"),),
            (("push", "origin", f"HEAD:refs/heads/{branch}"),),
        ]
        request_url, headers, body = http.call_args.args
        assert request_url == (
            "https://dev.azure.com/<org>/<project-id>/_apis/git/repositories/"
            "<repo-id>/pullrequests?api-version=7.1"
        )
        assert headers == {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }
        assert json.loads(body) == {
            "sourceRefName": f"refs/heads/{branch}",
            "targetRefName": "refs/heads/main",
            "title": f"Import my_ta {version} from nonprod",
            "description": "Created by build 8421.",
        }
        assert output.getvalue().splitlines()[-1] == (
            "https://dev.azure.com/<org>/<project>/_git/<app-id>/pullrequest/34"
        )
        assert not (package / "default" / "old.conf").exists()
        assert (package / "lookups" / "keep.csv").read_text() == "h\nmain\n"
        assert not (package / "lookups" / "new.csv").exists()
        assert not (package / "local" / "props.conf").exists()
        assert not (package / "local" / "data" / "ui" / "views" / "example.xml").exists()
        assert not (package / "users" / "admin" / "local" / "savedsearches.conf").exists()
        assert not (package / "metadata" / "local.meta").exists()
        datamodels = (package / "default" / "datamodels.conf").read_text(encoding="utf-8")
        assert "[Fast]\nacceleration = false" in datamodels and "acceleration = 1" not in datamodels
        saved = (package / "default" / "savedsearches.conf").read_text(encoding="utf-8")
        assert "populate_lookup" not in saved and "search = x" in saved
        assert output.getvalue().count("not allowed in Splunk Cloud apps") == 2
        props = (package / "default" / "props.conf").read_text(encoding="utf-8")
        assert "value = local" in props
        assert (package / "default" / "data" / "ui" / "views" / "example.xml").exists()
        assert "access = read : [*]" in (
            package / "metadata" / "default.meta"
        ).read_text(encoding="utf-8")
        app_conf = (package / "default" / "app.conf").read_text(encoding="utf-8")
        assert app_conf.count(f"version = {version}") == 2
        assert manifest.read_text(encoding="utf-8") == "generated manifest\n"


class ImportNonprodTests(TestCase):
    def test_import_nonprod(self):
        check_import_nonprod()


if __name__ == "__main__":
    check_import_nonprod()
    print("ok")

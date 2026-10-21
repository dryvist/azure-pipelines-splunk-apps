"""Tests for the import command."""

from unittest import TestCase

import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _common import CONF, write_tgz
from splunk_release import import_app


def check_import_app(environment, *flags):
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
        export_dir = root / "export"
        export_dir.mkdir()
        write_tgz(
            export_dir / "my_ta.tgz",
            {
                "my_ta/default/app.conf": CONF,
                "my_ta/default/props.conf": "[changed]\nvalue = default\n",
                "my_ta/local/props.conf": "[changed]\nvalue = local\n",
                "my_ta/lookups/keep.csv": "h\nexported\n",
                "my_ta/lookups/new.csv": "h\n1\n",
                "my_ta/lookups/lookup_file_backups/my_ta/nobody/new.csv/1700000000": "h\n1\n",
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
            patch("splunk_release.import_app.SRC", package),
            patch("splunk_release.import_app.CONF", main_conf),
            patch("splunk_release.import_app.APP", "my_ta"),
            patch("splunk_release.import_app.generate_manifest", side_effect=write_manifest) as generate,
            patch("splunk_release.import_app.git") as git,
            patch("splunk_release.import_app.feed_versions", return_value=["1.4.20", "1.4.3"]),
            patch("splunk_release.import_app.http", return_value=b'{"pullRequestId": 34, "createdBy": {"id": "build-id"}}') as http,
            patch.dict(os.environ, environment),
            redirect_stdout(output),
        ):
            import_app.import_app(environment, export_dir, *flags)

        version = "1.4.21"
        branch = f"{environment}-import/{version}-8421"
        generate.assert_called_once_with()
        assert git.call_args_list == [
            (("checkout", "-b", branch),),
            (("add", "--all", str(package)),),
            (("commit", "-m", f"Import my_ta {version} from {environment}"),),
            (("push", "origin", f"HEAD:refs/heads/{branch}"),),
        ]
        request_url, headers, body = http.call_args_list[0].args
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
            "title": f"Import my_ta {version} from {environment}",
            "description": "Created by build 8421.",
        }
        update_url, _, update = http.call_args.args
        assert update_url.endswith("/pullrequests/34?api-version=7.1") and http.call_args.kwargs == {"method": "PATCH"}
        assert json.loads(update) == {
            "autoCompleteSetBy": {"id": "build-id"},
            "completionOptions": {"deleteSourceBranch": True},
        }
        assert output.getvalue().splitlines()[-1] == (
            "https://dev.azure.com/<org>/<project>/_git/<app-id>/pullrequest/34"
        )
        assert not (package / "default" / "old.conf").exists()
        skipped = "--skip-lookups" in flags
        assert (package / "lookups" / "keep.csv").read_text() == ("h\nmain\n" if skipped else "h\nexported\n")
        assert (package / "lookups" / "new.csv").exists() != skipped
        assert (package / "lookups" / "lookup_file_backups").exists() == (not flags)
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


class ImportAppTests(TestCase):
    def test_import_app(self):
        check_import_app("nonprod", "--skip-lookups")
        check_import_app("prod", "--skip-lookup-backups")
        check_import_app("nonprod")


if __name__ == "__main__":
    check_import_app("nonprod", "--skip-lookups")
    check_import_app("prod", "--skip-lookup-backups")
    check_import_app("nonprod")
    print("ok")

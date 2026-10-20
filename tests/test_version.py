"""Tests for splunk_release.version."""

from unittest import TestCase

import io
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _common import CONF
from splunk_release import version as version_module
from splunk_release.version import bump_conf, bump_level, set_version


def check_version():
    # Bump helpers and AppInspect result gate.
    assert bump_level("Fix a bug") == "patch"
    assert bump_level("Add a feature [minor]") == "minor"
    assert bump_level("Breaking change [major]") == "major"
    text, version = bump_conf(CONF, "patch")
    assert version == "1.4.10"
    assert text == CONF.replace("1.4.9", "1.4.10")
    assert set_version(CONF, "2.3.4") == CONF.replace("1.4.9", "2.3.4")
    assert bump_conf(CONF, "minor")[1] == "1.5.0"
    assert bump_conf(CONF, "major")[1] == "2.0.0"
    # Tagging sets Azure Pipelines variables after pushing the version tag.
    with tempfile.TemporaryDirectory() as tmp:
        app_conf = Path(tmp, "app.conf")
        app_conf.write_text(CONF, encoding="utf-8")
        calls = []
        output = io.StringIO()
        with (
            patch("splunk_release.version.CONF", app_conf),
            patch("splunk_release.version.APP", "my_ta"),
            patch("splunk_release.version.git", side_effect=lambda *args: calls.append(args)),
            patch("splunk_release.version.published", return_value=False),
            redirect_stdout(output),
        ):
            version_module.tag()
        assert calls == [
            ("tag", "--force", "v1.4.9"),
            ("push", "origin", "refs/tags/v1.4.9"),
        ]
        assert output.getvalue().splitlines() == [
            "##vso[task.setvariable variable=APP_ID]my_ta",
            "##vso[task.setvariable variable=APP_VERSION]1.4.9",
        ]

    # The feed check maps the collection URL to the feeds host and matches the exact name and version.
    env = {"SYSTEM_COLLECTIONURI": "https://dev.azure.com/org/", "SYSTEM_TEAMPROJECTID": "p1",
           "SYSTEM_ACCESSTOKEN": "t"}
    body = b'{"value": [{"name": "my_ta_extra", "versions": [{"version": "1.4.9"}]}, ' \
           b'{"name": "my_ta", "versions": [{"version": "1.4.8"}]}]}'
    with patch.dict(os.environ, env), patch("splunk_release.version.http", return_value=body) as http:
        assert not version_module.published("my_ta", "1.4.9")
    assert http.call_args.args[0] == ("https://feeds.dev.azure.com/org/p1/_apis/packaging/feeds/splunk-apps/"
                                      "packages?protocolType=upack&packageNameQuery=my_ta"
                                      "&includeAllVersions=true&api-version=7.1")
    with patch.dict(os.environ, env), patch("splunk_release.version.http", return_value=body):
        assert version_module.published("my_ta", "1.4.8")
        version_module.feed_check("MY_TA")
        try:
            version_module.feed_check("other_ta")
            raise AssertionError("an app missing from the feed should exit")
        except SystemExit as error:
            assert "other_ta is not in the splunk-apps feed" in str(error)


class VersionTests(TestCase):
    def test_version(self):
        check_version()


if __name__ == "__main__":
    check_version()
    print("ok")

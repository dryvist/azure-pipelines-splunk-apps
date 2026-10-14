"""Tests for splunk_release.version."""

from unittest import TestCase

import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _common import CONF
from splunk_release import version as version_module
from splunk_release.version import bump_conf, bump_level


def check_version():
    # Bump helpers and AppInspect result gate.
    assert bump_level("Fix a bug") == "patch"
    assert bump_level("Add a feature [minor]") == "minor"
    assert bump_level("Breaking change [major]") == "major"
    text, version = bump_conf(CONF, "patch")
    assert version == "1.4.10"
    assert text == CONF.replace("1.4.9", "1.4.10")
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


class VersionTests(TestCase):
    def test_version(self):
        check_version()


if __name__ == "__main__":
    check_version()
    print("ok")

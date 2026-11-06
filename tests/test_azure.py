"""Tests for splunk_release.azure."""

from unittest import TestCase

import io
import json
import os
from contextlib import redirect_stdout
from unittest.mock import patch

from splunk_release import azure


def check_azure():
    # stages_succeeded stops unless every named stage succeeded in this run.
    env = {"SYSTEM_COLLECTIONURI": "https://dev.azure.com/<org>/", "SYSTEM_TEAMPROJECTID": "<project-id>",
           "BUILD_BUILDID": "7", "SYSTEM_ACCESSTOKEN": "t"}
    timeline = {"records": [{"type": "Stage", "identifier": "release", "result": "succeeded"},
                            {"type": "Stage", "identifier": "proddiff", "result": "failed"}]}
    with patch.dict(os.environ, env), patch("splunk_release.azure.http", return_value=json.dumps(timeline).encode()):
        with redirect_stdout(io.StringIO()):
            azure.stages_succeeded("release")
        try:
            azure.stages_succeeded("release", "proddiff")
        except SystemExit as error:
            assert "proddiff" in str(error)
        else:
            raise AssertionError("missing proddiff did not stop the run")

    # A missing value is one error line and exit code 1.
    output = io.StringIO()
    with redirect_stdout(output):
        try:
            azure.run_cli(lambda: {}["apps"])
        except SystemExit as error:
            assert error.code == 1
        else:
            raise AssertionError("a missing value did not stop the run")
    assert "KeyError: 'apps'" in output.getvalue()


class AzureTests(TestCase):
    def test_azure(self):
        check_azure()


if __name__ == "__main__":
    check_azure()
    print("ok")

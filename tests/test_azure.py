"""Tests for splunk_release.azure."""

from unittest import TestCase

import io
import json
import os
from contextlib import redirect_stdout
from unittest.mock import patch

from splunk_release import azure


def check_azure():
    # Deploy to prod stops unless release and proddiff succeeded in this run.
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


class AzureTests(TestCase):
    def test_azure(self):
        check_azure()


if __name__ == "__main__":
    check_azure()
    print("ok")

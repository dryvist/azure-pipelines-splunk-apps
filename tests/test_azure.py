"""Tests for splunk_release.azure."""

from unittest import TestCase

import _common
import io
import os
from contextlib import redirect_stdout
from unittest.mock import patch

from splunk_release import azure


def check_azure():
    # The stage plan runs compare and nonprod on pull requests and main.
    for env, runs in (
        ({"BUILD_REASON": "PullRequest", "BUILD_SOURCEBRANCH": "refs/heads/feature"}, {"nonprod", "proddiff"}),
        ({"BUILD_REASON": "IndividualCI", "BUILD_SOURCEBRANCH": "refs/heads/main"}, {"nonprod", "proddiff", "release"}),
    ):
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), redirect_stdout(output):
            azure.plan()
        shown = {line.split()[0] for line in output.getvalue().splitlines() if " RUNS " in line}
        assert shown == {"build", "appinspect"} | runs


class AzureTests(TestCase):
    def test_azure(self):
        check_azure()


if __name__ == "__main__":
    check_azure()
    print("ok")

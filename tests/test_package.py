"""Tests for splunk_release.package."""

from unittest import TestCase

import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from splunk_release import package


def check_package():
    # Package stages the source and calls the Splunk Packaging Toolkit CLI.
    with tempfile.TemporaryDirectory() as tmp:
        stage, dist = Path(tmp, "build", "my_ta"), Path(tmp, "dist")
        with (
            patch("splunk_release.package.STAGE", stage),
            patch("splunk_release.package.DIST", dist),
            patch("splunk_release.package.stage") as stage_source,
            patch("splunk_release.package.run") as run,
        ):
            package.package()
        stage_source.assert_called_once_with()
        assert run.call_args.args[0] == [
            "slim",
            "package",
            str(stage),
            "-o",
            str(dist),
        ]
        assert run.call_args.kwargs["check"] is True

    # Sorting orders stanzas and keys with one blank line between stanzas.
    with tempfile.TemporaryDirectory() as tmp:
        conf = Path(tmp, "default", "props.conf")
        conf.parent.mkdir()
        conf.write_text("[zeta]\nb = 2\na = 1\n\n\n[alpha]\nx = 8\n")
        with redirect_stdout(io.StringIO()):
            package.sort_confs(tmp)
        assert conf.read_text() == "[alpha]\nx = 8\n\n[zeta]\na = 1\nb = 2\n"


class PackageTests(TestCase):
    def test_package(self):
        check_package()


if __name__ == "__main__":
    check_package()
    print("ok")

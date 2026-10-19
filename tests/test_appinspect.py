"""Tests for splunk_release.appinspect."""

from unittest import TestCase

import io
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from splunk_release import appinspect


def check_appinspect():
    clean = {"summary": {"failure": 0, "error": 0, "manual_check": 0}}
    assert appinspect.appinspect_passed("SUCCESS", clean)
    assert not appinspect.appinspect_passed("FAILURE", clean)
    for count in ("failure", "error", "manual_check"):
        assert not appinspect.appinspect_passed(
            "SUCCESS", {"summary": {**clean["summary"], count: 1}}
        )
    out = io.StringIO()
    with redirect_stdout(out):
        appinspect.print_summary("SUCCESS", {"failure": 2, "warning": 5})
    blocking, other = out.getvalue().split("##[section]Does not block deployment\n")
    assert '"failure": 2' in blocking and '"status": "SUCCESS"' in blocking
    assert '"warning": 5' in other and "failure" not in other
    # AppInspect multipart packaging retains the uploaded filename and bytes.
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp, "app.tgz")
        pkg_bytes = b"app package bytes"
        pkg.write_bytes(pkg_bytes)
        _, body = appinspect.multipart(pkg)
        assert b'name="app_package"; filename="app.tgz"' in body
        assert pkg_bytes in body


class AppinspectTests(TestCase):
    def test_appinspect(self):
        check_appinspect()


if __name__ == "__main__":
    check_appinspect()
    print("ok")

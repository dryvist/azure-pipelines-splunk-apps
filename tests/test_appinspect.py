"""Tests for splunk_release.appinspect."""

from unittest import TestCase

import io
import json
import tempfile
import os
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from splunk_release import appinspect


@patch.dict(os.environ, {"TF_BUILD": "1"})
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
    # The shown report marks failure and error lines red and lists every check that did not pass.
    checks = [
        {"name": "check_a", "result": "failure", "messages": [{"message": "bad", "message_filename": "default/app.conf", "message_line": 3}]},
        {"name": "check_b", "result": "success", "messages": []},
        {"name": "check_c", "result": "warning", "messages": [{"message": "meh"}]},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "appinspect-report.json")
        path.write_text(json.dumps({"reports": [{"groups": [{"checks": checks}]}]}), encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            appinspect.show_report(path)
    text = out.getvalue()
    assert any(l.startswith("##[error] ") and '"result": "failure"' in l for l in text.splitlines())
    assert "##[error]failure: check_a\n    default/app.conf:3 bad\n" in text
    assert "##[warning]warning: check_c\n    meh\n" in text and "check_b\n" not in text
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

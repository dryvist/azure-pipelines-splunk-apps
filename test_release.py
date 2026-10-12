"""python test_release.py — self-check for release.py (version bump, multipart body)."""

import io
import json
import os
import subprocess
import tarfile
import tempfile
from contextlib import redirect_stdout
from email.parser import BytesParser
from email.policy import default
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import release
from release import app_id, bump_conf, bump_level, multipart

CONF = """# keep me
[install]
is_configured = 0

[launcher]
version = 1.4.9
description = keep me too

[id]
name = my_ta
version = 1.4.9
"""

assert bump_level("Merged PR 12: add input") == "patch"
assert bump_level("Merged PR 13: new feature [Minor]") == "minor"
assert bump_level("[major] breaking change") == "major"

text, new = bump_conf(CONF, "patch")
assert new == "1.4.10" and text == CONF.replace("1.4.9", "1.4.10"), text
assert bump_conf(CONF, "minor")[1] == "1.5.0"
assert bump_conf(CONF, "major")[1] == "2.0.0"

for broken in (
    CONF.replace("version = 1.4.9\nd", "d"),
    CONF.replace("version = 1.4.9\n", "version = 1.4.8\n", 1),
):
    try:
        bump_conf(broken, "patch")
    except SystemExit:
        pass
    else:
        raise AssertionError(f"accepted broken app.conf:\n{broken}")


def run_bump(target_text, target_ref="refs/heads/main"):
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path.cwd()
        git_calls, show_calls = [], []
        try:
            os.chdir(tmp)
            Path("package/default").mkdir(parents=True)
            Path("package/default/app.conf").write_text(CONF)
            Path(release.STAGE, release.MANIFEST.name).parent.mkdir(parents=True)
            Path(release.STAGE, release.MANIFEST.name).touch()

            def fake_show(args, **kwargs):
                show_calls.append(args)
                if target_text is None:
                    raise subprocess.CalledProcessError(128, args)
                return target_text

            env = {
                "SYSTEM_PULLREQUEST_TARGETBRANCH": target_ref,
                "SYSTEM_PULLREQUEST_SOURCEBRANCH": "refs/heads/feature/release",
                "BUILD_SOURCEVERSIONMESSAGE": "Feature",
            }
            with (
                patch.dict(os.environ, env, clear=True),
                patch("release.git", side_effect=lambda *args: git_calls.append(args)),
                patch("release.stage"),
                patch("release.slim"),
                patch("release.subprocess.check_output", side_effect=fake_show),
            ):
                output = StringIO()
                with redirect_stdout(output):
                    release.bump()
                app_conf = Path("package/default/app.conf").read_text()
            return app_conf, git_calls, show_calls, output.getvalue()
        finally:
            os.chdir(cwd)


target_differs = CONF.replace("1.4.9", "1.4.8")
app_conf, git_calls, show_calls, output = run_bump(target_differs)
assert "version already changed, skipping bump" in output
assert app_conf == CONF
assert [c[0] for c in git_calls] == ["fetch", "checkout"], git_calls
assert show_calls[0][-1] == "origin/main:package/default/app.conf", show_calls

app_conf, git_calls, _, output = run_bump(CONF)
assert release.current_version(app_conf.splitlines()) == "1.4.10"
assert "bumped to 1.4.10" in output
commit = " ".join(next(call for call in git_calls if "commit" in call))
assert "Release" in commit and "1.4.10" in commit and "***NO_CI***" not in commit
assert git_calls[-1] == ("push", "origin", "HEAD:refs/heads/feature/release")

app_conf, git_calls, _, output = run_bump(None)
assert app_conf == CONF and [c[0] for c in git_calls] == ["fetch", "checkout"]
assert "target app.conf is missing, skipping bump" in output

with tempfile.TemporaryDirectory() as tmp:
    cwd = Path.cwd()
    try:
        os.chdir(tmp)
        with patch.dict(os.environ, {}, clear=True), patch("release.git") as git_mock:
            output = StringIO()
            with redirect_stdout(output):
                release.bump()
        assert "not a PR validation build, skipping bump" in output.getvalue()
        git_mock.assert_not_called()
    finally:
        os.chdir(cwd)

assert release.appinspect_passed("SUCCESS", {"summary": {"failure": 0, "error": 0}})
assert not release.appinspect_passed("FAILURE", {"summary": {"failure": 0, "error": 0}})
assert not release.appinspect_passed("SUCCESS", {"summary": {"failure": 1, "error": 0}})
assert not release.appinspect_passed("SUCCESS", {"summary": {"failure": 0, "error": 1}})

with tempfile.TemporaryDirectory() as tmp:
    report = {"summary": {"failure": 0, "error": 0}}
    output = StringIO()
    with redirect_stdout(output):
        release.save_appinspect_report(tmp, b"<html>report</html>", report)
    report_json = Path(tmp, "appinspect-report.json").read_text()
    assert report_json == json.dumps(report, indent=2) + "\n"
    assert '\n  "summary"' in report_json
    assert Path(tmp, "appinspect-report.html").read_bytes() == b"<html>report</html>"

with tempfile.TemporaryDirectory() as tmp:
    pkg = Path(tmp, "my_app-1.0.0.tar.gz")
    pkg.write_bytes(b"\x1f\x8b binary \r\n--not-a-boundary")
    content_type, body = multipart(token="abc", package=pkg)
    msg = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + body
    )
    parts = {
        p.get_param("name", header="content-disposition"): p for p in msg.iter_parts()
    }
    assert parts["token"].get_content() == "abc", parts["token"]
    assert parts["package"].get_filename() == pkg.name
    assert parts["package"].get_content() == pkg.read_bytes()

with tempfile.TemporaryDirectory() as tmp:
    cwd = Path.cwd()
    os.chdir(tmp)
    try:
        os.environ.pop("BUILD_REPOSITORY_NAME", None)
        assert app_id() == Path.cwd().name, app_id()
        Path("package/default").mkdir(parents=True)
        Path("package/default/app.conf").write_text(CONF)
        assert app_id() == "my_ta", app_id()
    finally:
        os.chdir(cwd)


def write_tgz(path, files):
    with tarfile.open(path, "w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


with tempfile.TemporaryDirectory() as tmp:
    pkg_dir, export_dir, out_dir = (Path(tmp, d) for d in ("dist", "export", "out"))
    pkg_dir.mkdir()
    export_dir.mkdir()
    write_tgz(
        pkg_dir / "my_ta-1.4.10.tar.gz",
        {
            "my_ta/default/app.conf": "version = 1.4.10\n",
            "my_ta/default/new.conf": "x\n",
        },
    )
    write_tgz(
        export_dir / "my_ta-export.tgz",
        {
            "my_ta/default/app.conf": "version = 1.4.9\n",
            "my_ta/local/props.conf": "ui\n",
        },
    )
    with redirect_stdout(StringIO()):
        release.diff(pkg_dir, export_dir, out_dir)
    patch_text = (out_dir / "prod-diff.patch").read_text()
    summary = (out_dir / "prod-diff-summary.txt").read_text()
    assert "-version = 1.4.9" in patch_text and "+version = 1.4.10" in patch_text, (
        patch_text
    )
    assert "+x" in patch_text and "-ui" in patch_text, patch_text
    assert summary.count("differ") == 3, summary
    assert sorted(p.name for p in out_dir.iterdir()) == [
        "prod-diff-summary.txt",
        "prod-diff.patch",
    ]

    # Not installed in production: every package file is an addition.
    (export_dir / "my_ta-export.tgz").unlink()
    with redirect_stdout(StringIO()):
        release.diff(pkg_dir, export_dir, out_dir)
    assert "+version = 1.4.10" in (out_dir / "prod-diff.patch").read_text()


def run_tag(ls_remote, head="c" * 40):
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path.cwd()
        git_calls = []
        try:
            os.chdir(tmp)
            Path("package/default").mkdir(parents=True)
            Path("package/default/app.conf").write_text(CONF)

            def fake_output(args, **kwargs):
                return head + "\n" if args[1] == "rev-parse" else ls_remote

            with (
                patch.dict(os.environ, {"BUILD_REASON": "IndividualCI"}, clear=True),
                patch("release.git", side_effect=lambda *a: git_calls.append(a)),
                patch("release.subprocess.check_output", side_effect=fake_output),
                redirect_stdout(StringIO()),
            ):
                release.tag()
            return git_calls
        finally:
            os.chdir(cwd)


calls = run_tag("")
assert calls[0][-4:] == ("-a", "v1.4.9", "-m", f"{release.APP} v1.4.9"), calls
assert calls[-1] == ("push", "origin", "refs/tags/v1.4.9"), calls
assert (
    run_tag(f"{'t' * 40}\trefs/tags/v1.4.9\n{'c' * 40}\trefs/tags/v1.4.9^{{}}\n") == []
)
try:
    run_tag(f"{'t' * 40}\trefs/tags/v1.4.9\n{'d' * 40}\trefs/tags/v1.4.9^{{}}\n")
except SystemExit as e:
    assert "bump the version" in str(e), e
else:
    raise AssertionError("tag accepted a version already tagged on another commit")

print("ok")

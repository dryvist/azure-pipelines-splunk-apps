"""Tests for splunk_release.acs."""

from unittest import TestCase

import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from splunk_release import acs


def structured(response):
    return json.dumps([{"response": json.dumps(response)}])


@patch.dict(os.environ, {"TF_BUILD": "1"})
def check_acs():
    # ACS setup downloads the platform archive, verifies it, adds the stack, and logs in.
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w:gz") as archive:
        info = tarfile.TarInfo("acs")
        info.size = 7
        archive.addfile(info, io.BytesIO(b"acs cli"))

    def fake_run(cmd, **_):
        if cmd[0] == "curl":
            Path(cmd[-2]).write_bytes(payload.getvalue())
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    good = "9450ee04be42c633af4b0db932d28139232815704bc4410c0908ea8ee38a8e49"
    for checksum, search_head in ((good, None), (good, "premium-sh"), (good, "$(SPLUNK_SEARCH_HEAD)"), ("bad", None)):
        variables = {"SPLUNK_STACK": "example-stack", "PATH": os.environ["PATH"]}
        if search_head is not None:
            variables["SPLUNK_SEARCH_HEAD"] = search_head
        with tempfile.TemporaryDirectory() as tmp:
            variables["AGENT_TEMPDIRECTORY"] = tmp
            output = io.StringIO()
            with (
                patch.dict(os.environ, variables, clear=True),
                patch("splunk_release.acs.os.name", "posix"),
                patch("splunk_release.acs.run", side_effect=fake_run) as run,
                patch("splunk_release.acs.hashlib.sha256") as sha256,
                redirect_stdout(output),
            ):
                sha256.return_value.hexdigest.return_value = checksum
                try:
                    acs.install_acs()
                except SystemExit as error:
                    assert checksum == "bad" and "checksum mismatch" in str(error)
                    continue
                home = acs.acs_env()["HOME"]
            commands = [call.args[0] for call in run.call_args_list]
            assert commands[0][-1].endswith("/v2.26.0/acs_v2.26.0_linux_amd64.tar.gz")
            target = ["--target-sh=premium-sh"] if search_head == "premium-sh" else []
            assert commands[1:] == [
                ["acs", "version"],
                ["acs", "config", "add-stack", "example-stack", "--use", *target],
                ["acs", "login"],
            ]
            assert all(call.kwargs["env"]["HOME"] == home for call in run.call_args_list[1:])
            assert Path(tmp, "acs").read_bytes() == b"acs cli"
            assert f"##vso[task.prependpath]{tmp}" in output.getvalue()

    # A failed ACS command closes its group first, prints its output, and raises.
    with patch("splunk_release.acs.run") as run, redirect_stdout(io.StringIO()) as output:
        run.return_value = subprocess.CompletedProcess(["acs", "login"], 1, stdout="", stderr="Stack login failed")
        try:
            acs.acs({}, "login")
        except subprocess.CalledProcessError as error:
            assert error.returncode == 1
        else:
            raise AssertionError("expected CalledProcessError")
    assert output.getvalue().index("##[endgroup]") < output.getvalue().index("Stack login failed")

    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("splunk_release.acs.acs_env", return_value={}),
        patch("splunk_release.acs.run") as run,
    ):
        run.return_value = subprocess.CompletedProcess(
            ["acs"], 0, stdout=structured({"messages": {"restartRequired": True}}), stderr=""
        )
        output = io.StringIO()
        with redirect_stdout(output):
            acs.status()
        assert run.call_args.args[0] == ["acs", "status", "current-stack", "-f", "structured"]
        assert "##[warning]Restart required on stack" in output.getvalue()
        assert "##[group]acs status current-stack -f structured" in output.getvalue()
        assert "##[endgroup]" in output.getvalue()
        assert '"restartRequired": true' in output.getvalue()

    # Status fails when the output has no "response" JSON.
    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("splunk_release.acs.acs_env", return_value={}),
        patch("splunk_release.acs.run") as run,
        redirect_stdout(io.StringIO()) as output,
    ):
        run.return_value = subprocess.CompletedProcess(["acs"], 0, stdout="[{}]", stderr="")
        try:
            acs.status()
        except SystemExit:
            pass
        else:
            raise AssertionError("expected SystemExit")
    assert '##[error]acs status output has no JSON "response" object' in output.getvalue()

    # Restart polls restartRequired every 30 seconds until it clears.
    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("splunk_release.acs.acs_env", return_value={}),
        patch("splunk_release.acs.run") as run,
    ):
        run.side_effect = [
            subprocess.CompletedProcess(["acs"], 0, stdout=structured({"messages": {"restartRequired": True}}), stderr=""),
            subprocess.CompletedProcess(["acs"], 0, stdout="", stderr=""),
            subprocess.CompletedProcess(["acs"], 0, stdout=structured({"messages": {"restartRequired": True}}), stderr=""),
            subprocess.CompletedProcess(["acs"], 0, stdout=structured({"messages": {"restartRequired": False}}), stderr=""),
        ]
        now = [0]
        with patch("splunk_release.acs.time.monotonic", side_effect=lambda: now[0]), patch(
            "splunk_release.acs.time.sleep", side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)
        ), redirect_stdout(io.StringIO()):
            acs.restart()
        assert [call.args[0] for call in run.call_args_list] == [
            ["acs", "status", "current-stack", "-f", "structured"],
            ["acs", "restart", "current-stack"],
            ["acs", "status", "current-stack", "-f", "structured"],
            ["acs", "status", "current-stack", "-f", "structured"],
        ]
        assert now == [30]

    # Restart is skipped when no restart is required.
    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("splunk_release.acs.acs_env", return_value={}),
        patch("splunk_release.acs.run") as run,
        redirect_stdout(io.StringIO()) as output,
    ):
        run.return_value = subprocess.CompletedProcess(
            ["acs"], 0, stdout=structured({"messages": {"restartRequired": False}}), stderr=""
        )
        acs.restart()
    assert [call.args[0] for call in run.call_args_list] == [["acs", "status", "current-stack", "-f", "structured"]]
    assert "No restart required on stack" in output.getvalue()

    # The package filename supplies the app id and version for install and polling.
    with tempfile.TemporaryDirectory() as tmp:
        package_dir = Path(tmp, "my-app")
        package_dir.mkdir()
        (package_dir / "my-app-1.4.10.tar.gz").write_bytes(b"package")
        assert acs.package_identity(package_dir)[1:] == ("my-app", "1.4.10")
        with (
            patch.dict(os.environ, {"SPLUNK_STACK": "stack", "AGENT_TEMPDIRECTORY": tmp}),
            patch("splunk_release.acs.run") as run,
            redirect_stdout(io.StringIO()),
        ):
            run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            acs.deploy(package_dir)
        assert run.call_args.args[0][-2:] == ["--app-package", str(package_dir / "my-app-1.4.10.tar.gz")]

        # Uninstall runs only when the stack lists the app.
        for listed, calls in ((["my-app"], 1), (["other"], 0)):
            with (
                patch.dict(os.environ, {"SPLUNK_STACK": "stack", "AGENT_TEMPDIRECTORY": tmp}),
                patch("splunk_release.acs.listed_apps", return_value=listed),
                patch("splunk_release.acs.run") as run,
                redirect_stdout(io.StringIO()),
            ):
                run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
                acs.uninstall(package_dir)
            assert run.call_count == calls
            if calls:
                assert run.call_args.args[0] == ["acs", "apps", "uninstall", "my-app"]

        with (
            patch("splunk_release.acs.acs_env", return_value={}),
            patch("splunk_release.acs.run") as run,
        ):
            run.side_effect = [
                subprocess.CompletedProcess([], 0, stdout="version 1.4.9", stderr=""),
                subprocess.CompletedProcess([], 0, stdout="version 1.4.10", stderr=""),
            ]
            now, sleeps = [0], []
            def wait(seconds):
                sleeps.append(seconds)
                now[0] += seconds
            with patch("splunk_release.acs.time.monotonic", side_effect=lambda: now[0]), patch(
                "splunk_release.acs.time.sleep", side_effect=wait
            ), redirect_stdout(io.StringIO()):
                acs.wait_version(package_dir)
            assert run.call_count == 2 and sleeps == [3]

        with (
            patch("splunk_release.acs.acs_env", return_value={}),
            patch("splunk_release.acs.run") as run,
            patch("splunk_release.acs.time.sleep", side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)),
            patch("splunk_release.acs.time.monotonic", side_effect=lambda: now[0]),
            redirect_stdout(io.StringIO()),
        ):
            run.return_value = subprocess.CompletedProcess([], 0, stdout="version 1.4.9", stderr="")
            now[0] = 0
            try:
                acs.wait_version(package_dir)
            except SystemExit as error:
                assert error.code == 1
            else:
                raise AssertionError("version wait should time out")
            assert now == [300]

    # Custom export pages in blocks of 100 and excludes Splunkbase names.
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp, "exports")
        pages = []

        def fake_acs(command, **kwargs):
            if command[1:3] == ["apps", "list"]:
                offset = int(command[command.index("--offset") + 1])
                splunkbase = "--splunkbase=true" in command
                pages.append((splunkbase, offset))
                rows = [{"name": "base_app"}] if splunkbase else (
                    [{"name": f"custom_{i}"} for i in range(100)] if offset == 0
                    else [{"name": "base_app"}]
                )
                return subprocess.CompletedProcess(command, 0, json.dumps({"apps": rows}), "")
            if command[1:3] == ["apps", "export"]:
                app = json.loads(Path(command[3].split("=", 1)[1]).read_text())["Apps"][0]
                destination = Path(command[-1].split("=", 1)[1])
                (destination / f"{app}.tar.gz").write_bytes(b"export")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("splunk_release.acs.acs_env", return_value={}), patch("splunk_release.acs.run", side_effect=fake_acs), redirect_stdout(io.StringIO()):
            acs.export(out, "--custom")
        assert pages == [(False, 0), (False, 100), (True, 0)]
        assert len(list(out.glob("*.tgz"))) == 100

    with tempfile.TemporaryDirectory() as tmp:
        raw = '{"items":[]}'
        output = io.StringIO()
        with patch("splunk_release.acs.acs_env", return_value={}), patch(
            "splunk_release.acs.run", return_value=subprocess.CompletedProcess([], 0, raw, "")
        ), redirect_stdout(output):
            try:
                acs.export(Path(tmp), "--custom")
            except SystemExit as error:
                assert error.code == 1
            else:
                raise AssertionError("missing apps field should fail")
        assert raw in output.getvalue()

    # Package-directory export sets the Azure app id from the archive name.
    with tempfile.TemporaryDirectory() as tmp:
        package_dir = Path(tmp, "packages")
        package_dir.mkdir()
        (package_dir / "my-app-1.4.10.tar.gz").write_bytes(b"package")
        output = io.StringIO()

        def fake_export(command, **kwargs):
            if command[1:3] == ["apps", "export"]:
                app = json.loads(Path(command[3].split("=", 1)[1]).read_text())["Apps"][0]
                destination = Path(command[-1].split("=", 1)[1])
                (destination / f"{app}.tar.gz").write_bytes(b"export")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("splunk_release.acs.acs_env", return_value={}), patch(
            "splunk_release.acs.run", side_effect=fake_export
        ), redirect_stdout(output):
            acs.export(Path(tmp, "export"), package_dir)
        assert Path(tmp, "export", "my-app", "my-app.tgz").exists()
        assert "##vso[task.setvariable variable=APP_ID]my-app" in output.getvalue()

    # An app missing from the stack exports nothing and prints NOT INSTALLED.
    with tempfile.TemporaryDirectory() as tmp:
        missing = subprocess.CompletedProcess([], 1, "", "Failed in app_export with: APP_NOT_FOUND: New_App")
        output = io.StringIO()
        with patch("splunk_release.acs.acs_env", return_value={}), patch(
            "splunk_release.acs.run", return_value=missing
        ), redirect_stdout(output):
            acs.export(Path(tmp), "New_App")
        assert "NOT INSTALLED New_App" in output.getvalue()
        assert not any(Path(tmp).glob("*.tgz"))

    # The smoke result command passes only when all three jobs succeeded.
    result_script = Path(__file__).resolve().parents[1] / "smoke-test" / "smoke_test.py"
    passed = subprocess.run(
        [sys.executable, str(result_script), "result", "Succeeded", "Succeeded", "Succeeded"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert passed.returncode == 0
    assert "RESULT: ALL PASS" in passed.stdout
    failed = subprocess.run(
        [sys.executable, str(result_script), "result", "Succeeded", "Failed", "Succeeded"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failed.returncode == 1
    assert "RESULT: ALL PASS" not in failed.stdout
    assert "RESULT: FAILED - open each failed job for its FAIL or Error line" in failed.stdout


class AcsTests(TestCase):
    def test_acs(self):
        check_acs()


if __name__ == "__main__":
    check_acs()
    print("ok")

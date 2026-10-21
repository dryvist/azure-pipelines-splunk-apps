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

from _common import CONF, write_tgz
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
    assert '##[error]acs status current-stack output has no JSON "response" object' in output.getvalue()

    # The app list reads the names in each page's "response" object.
    with patch("splunk_release.acs.run") as run, redirect_stdout(io.StringIO()):
        run.return_value = subprocess.CompletedProcess(
            ["acs"], 0, stdout=structured({"apps": [{"appID": "a1", "name": "a1"}, {"name": "b2"}]}), stderr=""
        )
        assert acs.listed_apps({}) == ["a1", "b2"]
        assert run.call_args.args[0] == ["acs", "apps", "list", "--count", "100", "--offset", "0", "-f", "structured"]

    # Restart polls every 15 seconds until restartRequired clears and the stack is ready.
    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("splunk_release.acs.acs_env", return_value={}),
        patch("splunk_release.acs.stack_ready", return_value=(True, "ready")),
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
        assert now == [15]

    # A 401 while the search head restarts is waited out; other ACS errors still fail.
    unauthorized = subprocess.CalledProcessError(2, ["acs"], "", "failed, code: 401 Unauthorized")
    with (
        patch("splunk_release.acs.stack_ready", side_effect=[unauthorized, (True, "ready")]),
        patch("splunk_release.acs.time.sleep") as sleep,
        redirect_stdout(io.StringIO()) as output,
    ):
        acs.wait_done({}, lambda: True, "restart of stack")
    assert sleep.call_count == 1 and "401 Unauthorized, as it does while" in output.getvalue()
    with patch("splunk_release.acs.stack_ready", side_effect=subprocess.CalledProcessError(2, ["acs"], "", "code: 500")):
        try:
            acs.wait_done({}, lambda: True, "restart of stack")
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError("a non-401 error should fail the wait")

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
        def write_package(conf_version):
            conf = f"[launcher]\nversion = {conf_version}\n[id]\nname = my-app\nversion = {conf_version}\n".encode()
            with tarfile.open(package_dir / "my-app-1.4.10.tar.gz", "w:gz") as archive:
                info = tarfile.TarInfo("my-app/default/app.conf")
                info.size = len(conf)
                archive.addfile(info, io.BytesIO(conf))

        write_package("1.4.10")
        assert acs.package_identity(package_dir)[1:] == ("my-app", "1.4.10")
        with (
            patch.dict(os.environ, {"SPLUNK_STACK": "stack", "AGENT_TEMPDIRECTORY": tmp}),
            patch("splunk_release.acs.run") as run,
            redirect_stdout(io.StringIO()),
        ):
            run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            acs.deploy(package_dir)
        assert run.call_args.args[0][-2:] == ["--app-package", str(package_dir / "my-app-1.4.10.tar.gz")]

        # A package whose app.conf version differs from its file name fails before the install.
        write_package("1.2.0")
        with patch("splunk_release.acs.run") as run, redirect_stdout(io.StringIO()) as out:
            try:
                acs.deploy(package_dir)
            except SystemExit:
                pass
            else:
                raise AssertionError("a mismatched package should fail")
        assert not run.called and "app.conf version 1.2.0, not 1.4.10" in out.getvalue()
        write_package("1.4.10")

        # Uninstall repeats until ACS returns 404.
        uninstalled = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        not_found = subprocess.CompletedProcess([], 1, stdout="", stderr="code: 404 Not Found")
        with (
            patch.dict(os.environ, {"SPLUNK_STACK": "stack", "AGENT_TEMPDIRECTORY": tmp}),
            patch("splunk_release.acs.stack_ready", return_value=(True, "ready")),
            patch("splunk_release.acs.time.sleep"),
            patch("splunk_release.acs.run", side_effect=[uninstalled, not_found]) as run,
            redirect_stdout(io.StringIO()) as out,
        ):
            acs.uninstall(package_dir)
        assert [call.args[0] for call in run.call_args_list] == [["acs", "apps", "uninstall", "my-app"]] * 2
        assert "my-app gone from stack (ready)" in out.getvalue()

        with (
            patch("splunk_release.acs.acs_env", return_value={}),
            patch("splunk_release.acs.run") as run,
        ):
            # 1.4.100 contains the text 1.4.10 but is a different version.
            run.side_effect = [
                subprocess.CompletedProcess([], 0, stdout=structured({"version": "1.4.100"}), stderr=""),
                subprocess.CompletedProcess([], 0, stdout=structured({"version": "1.4.10"}), stderr=""),
            ]
            now, sleeps = [0], []
            def wait(seconds):
                sleeps.append(seconds)
                now[0] += seconds
            with patch("splunk_release.acs.time.monotonic", side_effect=lambda: now[0]), patch(
                "splunk_release.acs.time.sleep", side_effect=wait
            ), patch("splunk_release.acs.stack_ready", side_effect=[(False, "pending"), (True, "ready"), (True, "ready")]
                     ), redirect_stdout(io.StringIO()) as out:
                acs.wait_version(package_dir)
            assert run.call_count == 2 and sleeps == [15, 15]
            assert "reports my-app version 1.4.100, expected 1.4.10" in out.getvalue()

        # A busy stack response is retried until ACS accepts the command.
        busy = subprocess.CompletedProcess([], 1, "", "424-failed-dependency: A deployment task is still in progress.")
        with (
            patch("splunk_release.acs.run", side_effect=[busy, subprocess.CompletedProcess([], 0, "ok", "")]) as run,
            patch("splunk_release.acs.time.sleep") as sleep,
            redirect_stdout(io.StringIO()) as output,
        ):
            assert acs.acs({}, "apps", "uninstall", "my-app", main=True) == "ok"
        assert run.call_count == 2 and sleep.call_args.args == (30,)
        assert "ACS is busy" in output.getvalue()

        with (
            patch("splunk_release.acs.acs_env", return_value={}),
            patch("splunk_release.acs.run") as run,
            patch("splunk_release.acs.time.sleep", side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)),
            patch("splunk_release.acs.time.monotonic", side_effect=lambda: now[0]),
            patch("splunk_release.acs.stack_ready", return_value=(True, "ready")),
            redirect_stdout(io.StringIO()),
        ):
            run.return_value = subprocess.CompletedProcess([], 0, stdout=structured({"version": "1.4.9"}), stderr="")
            now[0] = 0
            try:
                acs.wait_version(package_dir)
            except SystemExit as error:
                assert error.code == 1
            else:
                raise AssertionError("version wait should time out")
            assert now == [900]

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
                return subprocess.CompletedProcess(command, 0, structured({"apps": rows}), "")
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


def check_stack_ready():
    response = {"infrastructure": {"status": "Ready"}}
    with patch("splunk_release.acs.stack_status", side_effect=lambda env: response):
        assert acs.stack_ready({}) == (True, "stack Ready")
        response["infrastructure"]["status"] = "Pending"
        assert acs.stack_ready({}) == (False, "stack Pending")
        response["infrastructure"]["status"] = "Failed"
        try:
            with redirect_stdout(io.StringIO()):
                acs.stack_ready({})
            raise AssertionError("expected SystemExit")
        except SystemExit as error:
            assert error.code == 1
    missing = subprocess.CalledProcessError(2, [], "", 'failed, code: 404 Not Found')
    with patch("splunk_release.acs.acs", side_effect=[
        structured({"version": "1.0.1"}), missing, subprocess.CalledProcessError(2, [], "", "code: 500")
    ]):
        assert acs.installed_version({}, "a") == "1.0.1" and acs.installed_version({}, "a") is None
        try:
            acs.installed_version({}, "a")
            raise AssertionError("expected CalledProcessError")
        except subprocess.CalledProcessError:
            pass


@patch.dict(os.environ, {"SPLUNK_STACK": "stack", "SPLUNK_SEARCH_HEAD": "", "SPLUNK_REST_URL": "",
                         "STACK_TOKEN": "token"})
def check_repair():
    assert json.loads(acs.readable(structured({"apps": [{"name": "a"}]}))) == [{"response": {"apps": [{"name": "a"}]}}]
    assert acs.readable("App uninstalled successfully\n") == "App uninstalled successfully"
    assert acs.stanza_names(" a ; b c ;") == ["a", "b c"]
    with patch("splunk_release.acs.http", return_value=b"{}") as http:
        acs.rest("my_ta", "savedsearches", "Fix me/now", "DELETE")
    url, headers = http.call_args.args
    assert url == ("https://stack.splunkcloud.com:8089/servicesNS/nobody/my_ta/configs/conf-savedsearches/"
                   "Fix%20me%2Fnow?output_mode=json")
    assert headers == {"Authorization": "Bearer token"} and http.call_args.kwargs["method"] == "DELETE"
    with patch.dict(os.environ, {"SPLUNK_SEARCH_HEAD": "sh1"}):
        try:
            acs.rest("my_ta", "savedsearches", "x")
            raise AssertionError("expected SystemExit")
        except SystemExit as error:
            assert "SPLUNK_REST_URL" in str(error)

    with tempfile.TemporaryDirectory() as tmp:
        package_dir, out = Path(tmp, "dist"), Path(tmp, "repair")
        package_dir.mkdir()
        write_tgz(package_dir / "my_ta-1.4.9.tar.gz", {
            "my_ta/default/app.conf": CONF,
            "my_ta/default/savedsearches.conf": "[Keep]\nsearch = a\n\n[Fix me]\nsearch = b\n",
            "my_ta/app.manifest": json.dumps({"info": {"id": {"name": "my_ta", "version": "1.4.9"}}}),
        })
        output = io.StringIO()
        with (
            patch("splunk_release.acs.rest", return_value=b"{}"),
            patch("splunk_release.acs.acs_env", return_value={}),
            patch("splunk_release.acs.installed_version", return_value="1.4.11"),
            patch("splunk_release.acs.feed_versions", return_value=["1.4.9", "1.4.10"]),
            redirect_stdout(output),
        ):
            acs.repair_packages(package_dir, out, "savedsearches", "Fix me")
        assert "##vso[task.setvariable variable=REPAIR_VERSION]1.4.13" in output.getvalue()
        for folder, version, fixed in (("temp", "1.4.12", False), ("real", "1.4.13", True)):
            with tarfile.open(out / folder / f"my_ta-{version}.tar.gz") as archive:
                saved = archive.extractfile("my_ta/default/savedsearches.conf").read().decode()
                manifest = json.loads(archive.extractfile("my_ta/app.manifest").read())
                app_conf = archive.extractfile("my_ta/default/app.conf").read().decode()
            assert "[Keep]" in saved and ("[Fix me]" in saved) == fixed
            assert manifest["info"]["id"]["version"] == version and app_conf.count(f"version = {version}") == 2
        for rest, stanzas, message in ((b"{}", "Missing", "has no stanza [Missing]"), (None, "Fix me", "is not in")):
            with patch("splunk_release.acs.rest", return_value=rest), patch(
                "splunk_release.acs.installed_version", return_value="1.4.9"
            ), patch("splunk_release.acs.feed_versions", return_value=[]), patch("splunk_release.acs.acs_env"):
                try:
                    acs.repair_packages(package_dir, Path(tmp, "other"), "savedsearches", stanzas)
                    raise AssertionError("expected SystemExit")
                except SystemExit as error:
                    assert message in str(error)

        output = io.StringIO()
        with patch("splunk_release.acs.rest", side_effect=[b"{}", None]) as rest, redirect_stdout(output):
            acs.delete_local(package_dir, "savedsearches", "Fix me;Gone")
        assert [c.args for c in rest.call_args_list] == [("my_ta", "savedsearches", "Fix me", "DELETE"),
                                                         ("my_ta", "savedsearches", "Gone", "DELETE")]
        assert "Deleted the local copy of [Fix me]" in output.getvalue()
        assert "[Gone] has no local copy in my_ta" in output.getvalue()

        def export(out_dir, _):
            Path(out_dir, "my_ta").mkdir()
            write_tgz(Path(out_dir, "my_ta", "my_ta.tgz"), {"my_ta/local/savedsearches.conf": local})

        for local, failed in (("[Other]\nsearch = c\n", False), ("[Fix me]\nsearch = c\n", True)):
            with patch("splunk_release.acs.export", side_effect=export), patch(
                "splunk_release.acs.rest", return_value=b"{}"
            ), redirect_stdout(io.StringIO()):
                try:
                    acs.repair_check(package_dir, "savedsearches", "Fix me")
                    assert not failed
                except SystemExit as error:
                    assert failed and "[Fix me] still has a local copy" in str(error)


class AcsTests(TestCase):
    def test_acs(self):
        check_acs()

    def test_repair(self):
        check_repair()

    def test_stack_ready(self):
        check_stack_ready()


if __name__ == "__main__":
    check_acs()
    check_repair()
    check_stack_ready()
    print("ok")

"""Tests for release helpers; run with python test_release.py."""

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

import release
from release import bump_conf, bump_level

CONF = """[launcher]
version = 1.4.9
description = keep me

[id]
name = my_ta
version = 1.4.9
"""


# Bump helpers and AppInspect result gate.
assert bump_level("Fix a bug") == "patch"
assert bump_level("Add a feature [minor]") == "minor"
assert bump_level("Breaking change [major]") == "major"
text, version = bump_conf(CONF, "patch")
assert version == "1.4.10"
assert text == CONF.replace("1.4.9", "1.4.10")
assert bump_conf(CONF, "minor")[1] == "1.5.0"
assert bump_conf(CONF, "major")[1] == "2.0.0"

clean = {"summary": {"failure": 0, "error": 0, "manual_check": 0}}
assert release.appinspect_passed("SUCCESS", clean)
assert not release.appinspect_passed("FAILURE", clean)
for count in ("failure", "error", "manual_check"):
    assert not release.appinspect_passed(
        "SUCCESS", {"summary": {**clean["summary"], count: 1}}
    )

# ACS install downloads this platform's pinned archive, unpacks it, and rejects a bad checksum.
payload = io.BytesIO()
with tarfile.open(fileobj=payload, mode="w:gz") as archive:
    info = tarfile.TarInfo("acs")
    info.size = 7
    archive.addfile(info, io.BytesIO(b"acs cli"))
for checksum in ("9450ee04be42c633af4b0db932d28139232815704bc4410c0908ea8ee38a8e49", "bad"):
    with tempfile.TemporaryDirectory() as tmp:
        output = io.StringIO()
        with (
            patch.dict(os.environ, {"AGENT_TEMPDIRECTORY": tmp}),
            patch("release.os.name", "posix"),
            patch("release.run", side_effect=lambda cmd, **_: Path(cmd[-2]).write_bytes(payload.getvalue())) as curl,
            patch("release.hashlib.sha256") as sha256,
            redirect_stdout(output),
        ):
            sha256.return_value.hexdigest.return_value = checksum
            try:
                release.install_acs()
            except SystemExit as error:
                assert checksum == "bad" and "checksum mismatch" in str(error)
            else:
                assert checksum != "bad"
                assert curl.call_args.args[0][-1].endswith("/v2.26.0/acs_v2.26.0_linux_amd64.tar.gz")
                assert Path(tmp, "acs").read_bytes() == b"acs cli"
                assert f"##vso[task.prependpath]{tmp}" in output.getvalue()


def write_tgz(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


# Package stages the source and calls the Splunk Packaging Toolkit CLI.
with tempfile.TemporaryDirectory() as tmp:
    stage, dist = Path(tmp, "build", "my_ta"), Path(tmp, "dist")
    with (
        patch("release.APP", "my_ta"),
        patch("release.STAGE", stage),
        patch("release.DIST", dist),
        patch("release.stage") as stage_source,
        patch("release.subprocess.run") as run,
    ):
        release.package()
    stage_source.assert_called_once_with()
    assert run.call_args.args[0] == [
        "slim",
        "package",
        str(stage),
        "-o",
        str(dist),
    ]
    assert run.call_args.kwargs["check"] is True


# AppInspect multipart packaging retains the uploaded filename and bytes.
with tempfile.TemporaryDirectory() as tmp:
    pkg = Path(tmp, "app.tgz")
    pkg_bytes = b"app package bytes"
    pkg.write_bytes(pkg_bytes)
    _, body = release.multipart(pkg)
    assert b'name="app_package"; filename="app.tgz"' in body
    assert pkg_bytes in body


# ACS sessions and status use the shared command wrapper.
for search_head in (None, "", "premium-sh", "$(SPLUNK_SEARCH_HEAD)"):
    variables = {"SPLUNK_STACK": "example-stack"}
    if search_head is not None:
        variables["SPLUNK_SEARCH_HEAD"] = search_head
    with (
        patch.dict(os.environ, variables, clear=True),
        patch("release.run") as run,
        redirect_stdout(io.StringIO()),
    ):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with release.acs_session():
            pass
    commands = [call.args[0] for call in run.call_args_list]
    target = ["--target-sh=premium-sh"] if search_head == "premium-sh" else []
    assert commands == [
        ["acs", "config", "add-stack", "example-stack", "--use", *target],
        ["acs", "login"],
    ]
    assert all(call.kwargs["check"] for call in run.call_args_list)

with (
    patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
    patch("release.acs_session") as session,
    patch("release.run") as run,
):
    session.return_value.__enter__.return_value = {}
    run.return_value = subprocess.CompletedProcess(
        ["acs"], 0, stdout='{"Status":{"RestartRequired":true}}', stderr=""
    )
    output = io.StringIO()
    with redirect_stdout(output):
        release.status()
    assert run.call_args.args[0] == ["acs", "status", "current-stack", "-f", "structured"]
    assert "##[warning]Restart required on stack" in output.getvalue()
    assert "##[group]acs status current-stack -f structured" in output.getvalue()
    assert "##[endgroup]" in output.getvalue()

# Restart polls restartRequired every 30 seconds until it clears.
with (
    patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
    patch("release.acs_session") as session,
    patch("release.run") as run,
):
    session.return_value.__enter__.return_value = {}
    run.side_effect = [
        subprocess.CompletedProcess(["acs"], 0, stdout="", stderr=""),
        subprocess.CompletedProcess(["acs"], 0, stdout='{"restartRequired":true}', stderr=""),
        subprocess.CompletedProcess(["acs"], 0, stdout='{"restartRequired":false}', stderr=""),
    ]
    now = [0]
    with patch("release.time.monotonic", side_effect=lambda: now[0]), patch(
        "release.time.sleep", side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)
    ), redirect_stdout(io.StringIO()):
        release.restart()
    assert [call.args[0] for call in run.call_args_list] == [
        ["acs", "restart", "current-stack"],
        ["acs", "status", "current-stack", "-f", "structured"],
        ["acs", "status", "current-stack", "-f", "structured"],
    ]
    assert now == [30]

# The package filename supplies the app id and version for install and polling.
with tempfile.TemporaryDirectory() as tmp:
    package_dir = Path(tmp, "my-app")
    package_dir.mkdir()
    (package_dir / "my-app-1.4.10.tar.gz").write_bytes(b"package")
    assert release.package_identity(package_dir)[1:] == ("my-app", "1.4.10")
    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "stack"}),
        patch("release.run") as run,
        redirect_stdout(io.StringIO()),
    ):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        release.deploy(package_dir)
    assert run.call_args.args[0][-2:] == ["--app-package", str(package_dir / "my-app-1.4.10.tar.gz")]

    with (
        patch("release.acs_session") as session,
        patch("release.run") as run,
    ):
        session.return_value.__enter__.return_value = {}
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="version 1.4.9", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="version 1.4.10", stderr=""),
        ]
        now, sleeps = [0], []
        def wait(seconds):
            sleeps.append(seconds)
            now[0] += seconds
        with patch("release.time.monotonic", side_effect=lambda: now[0]), patch(
            "release.time.sleep", side_effect=wait
        ), redirect_stdout(io.StringIO()):
            release.wait_version(package_dir)
        assert run.call_count == 2 and sleeps == [3]

    with (
        patch("release.acs_session") as session,
        patch("release.run") as run,
        patch("release.time.sleep", side_effect=lambda seconds: now.__setitem__(0, now[0] + seconds)),
        patch("release.time.monotonic", side_effect=lambda: now[0]),
        redirect_stdout(io.StringIO()),
    ):
        session.return_value.__enter__.return_value = {}
        run.return_value = subprocess.CompletedProcess([], 0, stdout="version 1.4.9", stderr="")
        now[0] = 0
        try:
            release.wait_version(package_dir)
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

    with patch("release.acs_session") as session, patch("release.run", side_effect=fake_acs), redirect_stdout(io.StringIO()):
        session.return_value.__enter__.return_value = {}
        release.export(out, "--custom")
    assert pages == [(False, 0), (False, 100), (True, 0)]
    assert len(list(out.glob("*.tgz"))) == 100

with tempfile.TemporaryDirectory() as tmp:
    raw = '{"items":[]}'
    output = io.StringIO()
    with patch("release.acs_session") as session, patch(
        "release.run", return_value=subprocess.CompletedProcess([], 0, raw, "")
    ), redirect_stdout(output):
        session.return_value.__enter__.return_value = {}
        try:
            release.export(Path(tmp), "--custom")
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

    with patch("release.acs_session") as session, patch(
        "release.run", side_effect=fake_export
    ), redirect_stdout(output):
        session.return_value.__enter__.return_value = {}
        release.export(Path(tmp, "export"), package_dir)
    assert Path(tmp, "export", "my-app", "my-app.tgz").exists()
    assert "##vso[task.setvariable variable=APP_ID]my-app" in output.getvalue()


# Diff promotes local files, compares defaults, and archives the merged target.
with tempfile.TemporaryDirectory() as tmp:
    target_dir = Path(tmp, "target")
    source_dir = Path(tmp, "source")
    out = Path(tmp, "compare")
    target_dir.mkdir()
    source_dir.mkdir()
    write_tgz(
        target_dir / "my_ta.tgz",
        {
            "my_ta/default/props.conf": (
                "[changed]\nvalue = default\n"
            ),
            "my_ta/local/props.conf": (
                "[changed]\nvalue = local\n\n[new]\nvalue = added\n"
            ),
            "my_ta/local/data/ui/views/example.xml": "<view/>\n",
            "my_ta/metadata/local.meta": "[my_ta]\naccess = read : [*]\n",
            "my_ta/users/admin/local/savedsearches.conf": "[search]\n",
        },
    )
    write_tgz(
        source_dir / "my_ta-1.4.10.tar.gz",
        {
            "my_ta/default/props.conf": "[changed]\nvalue = package\n",
        },
    )
    output = io.StringIO()
    with redirect_stdout(output):
        release.diff(target_dir, source_dir, out)
    local_text = (out / "my_ta-local-vs-default.diff").read_text()
    html_text = (out / "my_ta-diff.html").read_text()
    assert "=== local/props.conf vs the same stanzas" in local_text
    assert "-value = package" in local_text and "+value = local" in local_text
    assert "[new]" in local_text
    assert "my_ta deployed diff" in html_text
    assert "default/" in html_text and "props.conf [changed]" in html_text
    assert '<table class="diff"' in html_text
    assert "Local vs default" in html_text and "same stanzas" in html_text
    assert "Added lines:" not in html_text
    patch_text = (out / "my_ta.patch").read_text()
    summary = (out / "my_ta-summary.md").read_text()
    patch_paths = [
        path
        for token in patch_text.split()
        if token.startswith(("target/", "source/"))
        for path in [token.split("\t", 1)[0]]
    ]
    assert patch_paths
    assert "--- target/default/props.conf" in patch_text
    assert "+++ source/default/props.conf" in patch_text
    assert "@@ " in patch_text, patch_text
    assert any(
        line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        for line in patch_text.splitlines()
    )
    assert all(
        path.startswith(("target/default/", "source/default/"))
        or path in (
            "target/metadata/default.meta",
            "source/metadata/default.meta",
        )
        for path in patch_paths
    )
    assert any(path.endswith("metadata/default.meta") for path in patch_paths)
    sections = [
        "## Deployed changes",
        "## Target local files (kept, not backed up)",
        "## Source local files (not deployed)",
        "## User files",
    ]
    assert [summary.index(section) for section in sections] == sorted(
        summary.index(section) for section in sections
    )
    assert "- Changed: default/props.conf" in summary
    assert "- Removed: metadata/default.meta" in summary
    assert "local/props.conf" in summary
    assert "metadata/local.meta" in summary
    assert "local/data/ui/views/example.xml" in summary
    assert "users/admin/local/savedsearches.conf" in summary
    assert "## Deployed change tree" in summary
    assert "  props.conf [changed]" in summary
    assert "##vso[task.uploadsummary]" in output.getvalue()
    assert output.getvalue().endswith(summary)
    merged_path = out / "my_ta-merged.tar.gz"
    assert merged_path.exists()
    with tarfile.open(merged_path, "r:gz") as archive:
        names = archive.getnames()
        assert all(name == "my_ta" or name.startswith("my_ta/") for name in names)
        assert not any("/local/" in name or "/users/" in name for name in names)
        assert "my_ta/metadata/local.meta" not in names
        merged_props = archive.extractfile("my_ta/default/props.conf").read().decode()
        assert "value = local" in merged_props
        assert "[new]" in merged_props
        assert "value = added" in merged_props
        assert archive.extractfile(
            "my_ta/default/data/ui/views/example.xml"
        ).read().decode() == "<view/>\n"
        assert "access = read : [*]" in archive.extractfile(
            "my_ta/metadata/default.meta"
        ).read().decode()


# The smoke result command passes only when all three jobs succeeded.
result_script = Path(__file__).parent / "smoke-test" / "smoke_test.py"
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


# Tagging sets Azure Pipelines variables after pushing the version tag.
with tempfile.TemporaryDirectory() as tmp:
    app_conf = Path(tmp, "app.conf")
    app_conf.write_text(CONF, encoding="utf-8")
    calls = []
    output = io.StringIO()
    with (
        patch("release.CONF", app_conf),
        patch("release.APP", "my_ta"),
        patch("release.git", side_effect=lambda *args: calls.append(args)),
        redirect_stdout(output),
    ):
        release.tag()
    assert calls == [
        ("tag", "--force", "v1.4.9"),
        ("push", "origin", "refs/tags/v1.4.9"),
    ]
    assert output.getvalue().splitlines() == [
        "##vso[task.setvariable variable=APP_ID]my_ta",
        "##vso[task.setvariable variable=APP_VERSION]1.4.9",
    ]

# Sorting orders stanzas and keys with one blank line between stanzas.
with tempfile.TemporaryDirectory() as tmp:
    conf = Path(tmp, "default", "props.conf")
    conf.parent.mkdir()
    conf.write_text("[zeta]\nb = 2\na = 1\n\n\n[alpha]\nx = 8\n")
    with redirect_stdout(io.StringIO()):
        release.sort_confs(tmp)
    assert conf.read_text() == "[alpha]\nx = 8\n\n[zeta]\na = 1\nb = 2\n"

# The stage plan runs compare and nonprod on pull requests and main.
for env, runs in (
    ({"BUILD_REASON": "PullRequest", "BUILD_SOURCEBRANCH": "refs/heads/feature"}, {"nonprod", "proddiff"}),
    ({"BUILD_REASON": "IndividualCI", "BUILD_SOURCEBRANCH": "refs/heads/main"}, {"nonprod", "proddiff", "release"}),
):
    output = io.StringIO()
    with patch.dict(os.environ, env, clear=True), redirect_stdout(output):
        release.plan()
    shown = {line.split()[0] for line in output.getvalue().splitlines() if " RUNS " in line}
    assert shown == {"build", "appinspect"} | runs

print("ok")

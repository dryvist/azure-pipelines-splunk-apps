"""Tests for release helpers; run with python test_release.py."""

import io
import json
import os
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


# ACS sessions select the configured search head only when its value is set.
for search_head in (None, "", "premium-sh", "$(SPLUNK_SEARCH_HEAD)"):
    variables = {"SPLUNK_STACK": "example-stack"}
    if search_head is not None:
        variables["SPLUNK_SEARCH_HEAD"] = search_head
    with (
        patch.dict(os.environ, variables, clear=True),
        patch("release.subprocess.run") as run,
    ):
        with release.acs_session():
            pass
    commands = [call.args[0] for call in run.call_args_list]
    expected = [["acs", "config", "add-stack", "example-stack", "--use"]]
    if search_head == "premium-sh":
        expected.append(
            ["acs", "config", "use-stack", "example-stack", "--target-sh=premium-sh"]
        )
    expected.append(["acs", "login"])
    assert commands == expected
    assert all(call.kwargs["check"] for call in run.call_args_list)


# Deploy scopes an install to the configured search head only when it is set.
for search_head, uses_target in (
    (None, False),
    ("premium-sh", True),
    ("$(SPLUNK_SEARCH_HEAD)", False),
):
    with tempfile.TemporaryDirectory() as tmp:
        package_dir = Path(tmp, "dist")
        package_dir.mkdir()
        (package_dir / "my_ta-1.4.10.tar.gz").write_bytes(b"package")
        variables = {
            "SPLUNK_STACK": "example-stack",
            "STACK_TOKEN": "token",
            "SPLUNK_USERNAME": "user",
            "SPLUNK_PASSWORD": "password",
        }
        if search_head is not None:
            variables["SPLUNK_SEARCH_HEAD"] = search_head
        with (
            patch.dict(os.environ, variables, clear=True),
            patch("release.subprocess.run") as run,
        ):
            release.deploy(package_dir)
        commands = [call.args[0] for call in run.call_args_list]
        expected = [
            ["acs", "config", "add-stack", "example-stack", "--use"],
        ]
        if uses_target:
            expected.append(
                ["acs", "config", "use-stack", "example-stack", "--target-sh=premium-sh"]
            )
        expected.extend(
            [
                ["acs", "login"],
                [
                    "acs",
                    "apps",
                    "install",
                    "private",
                    "--acs-legal-ack",
                    "Y",
                    "--app-package",
                    str(package_dir / "my_ta-1.4.10.tar.gz"),
                    *(["--scope", "local"] if uses_target else []),
                ],
            ]
        )
        assert commands == expected
        assert all(call.kwargs["check"] for call in run.call_args_list)


# Export writes one archive per installed app and reports apps with no export.
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp, "export")
    output = io.StringIO()

    def fake_acs(command, *, check, env):
        if command[1:3] == ["apps", "export"]:
            app = json.loads(Path(command[3].split("=", 1)[1]).read_text())["Apps"][0]
            if app == "my_ta":
                (out / f"{app}.tgz").write_bytes(b"export")

    with (
        patch.dict(os.environ, {"SPLUNK_STACK": "example-stack", "STACK_TOKEN": "token"}),
        patch("release.subprocess.run", side_effect=fake_acs) as run,
        redirect_stdout(output),
    ):
        release.export(out, "my_ta", "missing_ta")
    commands = [call.args[0] for call in run.call_args_list]
    input_file = out / "apps.json"
    assert commands == [
        ["acs", "config", "add-stack", "example-stack", "--use"],
        ["acs", "login"],
        [
            "acs",
            "apps",
            "export",
            f"--file={input_file}",
            "--default=true",
            "--local=true",
            "--users=true",
            "--confs-only=false",
            f"--export-dir={out}",
        ],
        [
            "acs",
            "apps",
            "export",
            f"--file={input_file}",
            "--default=true",
            "--local=true",
            "--users=true",
            "--confs-only=false",
            f"--export-dir={out}",
        ],
    ]
    assert (out / "my_ta.tgz").read_bytes() == b"export"
    assert not (out / "missing_ta.tgz").exists()
    assert output.getvalue() == "NOT INSTALLED missing_ta\n"
    assert not input_file.exists()


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
    patch_text = (out / "my_ta.patch").read_text()
    summary = (out / "my_ta-summary.md").read_text()
    patch_paths = [
        path
        for token in patch_text.split()
        if token.startswith(("target/", "source/"))
        for path in [token.split("\t", 1)[0]]
    ]
    assert patch_paths
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
    assert output.getvalue() == summary
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

print("ok")

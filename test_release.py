"""python test_release.py — checks the release helpers."""

import io
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

assert bump_level("Fix a bug") == "patch"
assert bump_level("Add a feature [minor]") == "minor"
assert bump_level("Breaking change [major]") == "major"

text, version = bump_conf(CONF, "patch")
assert version == "1.4.10"
assert text == CONF.replace("1.4.9", "1.4.10")
assert bump_conf(CONF, "minor")[1] == "1.5.0"
assert bump_conf(CONF, "major")[1] == "2.0.0"

clean = {"summary": {"failure": 0, "error": 0}}
assert release.appinspect_passed("SUCCESS", clean)
assert not release.appinspect_passed("FAILURE", clean)
assert not release.appinspect_passed("SUCCESS", {"summary": {"failure": 1, "error": 0}})
assert not release.appinspect_passed("SUCCESS", {"summary": {"failure": 0, "error": 1}})


def write_tgz(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


with tempfile.TemporaryDirectory() as tmp:
    dist, out = Path(tmp, "dist"), Path(tmp, "out")
    dist.mkdir()
    out.mkdir()
    write_tgz(
        dist / "my_ta-1.4.10.tar.gz",
        {
            "my_ta/default/app.conf": "version = 1.4.10\n",
            "my_ta/default/new.conf": "added\n",
        },
    )
    prod = out / f"{release.APP}-prod.tgz"
    write_tgz(
        prod,
        {
            "my_ta/default/app.conf": "version = 1.4.9\n",
            "my_ta/local/props.conf": "ui edit\n",
        },
    )
    release.diff(dist, out)
    diff_text = (out / "prod-diff.patch").read_text()
    assert "-version = 1.4.9" in diff_text
    assert "+version = 1.4.10" in diff_text
    assert "+added" in diff_text
    assert "-ui edit" in diff_text

    prod.unlink()
    release.diff(dist, out)
    assert "+version = 1.4.10" in (out / "prod-diff.patch").read_text()

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

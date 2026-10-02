"""python test_release.py — self-check for release.py (version bump, Classic multipart body)."""

import tempfile
from email.parser import BytesParser
from email.policy import default
from pathlib import Path

from release import bump_conf, bump_level, multipart

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

print("ok")

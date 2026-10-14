"""Shared test fixtures and repository import setup."""

import io
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CONF = """[launcher]
version = 1.4.9
description = keep me

[id]
name = my_ta
version = 1.4.9
"""

def write_tgz(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))

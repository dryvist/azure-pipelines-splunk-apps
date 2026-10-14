"""Stage and package the Splunk app."""

import os
import shutil
from pathlib import Path

from splunk_release.azure import run
from splunk_release.version import APP, DIST, MANIFEST, SRC, STAGE

# AppInspect rejects hidden files and compiled Python. Tests are excluded from the package.
EXCLUDE = shutil.ignore_patterns(".*", "__pycache__", "*.pyc", "*.pyo", "tests")

def sort_confs(root):
    """Sort stanzas and keys in every .conf file under root with ksconf, one blank line apart."""
    confs = sorted(str(p) for p in Path(root).rglob("*.conf"))
    if confs:
        # ksconf exits 9 when it rewrote a file.
        run(["ksconf", "sort", "--inplace", "--quiet", *confs], check=False)

def stage():
    """Copy package/ to build/<app>; slim requires the folder and tarball root to match the app id."""
    shutil.rmtree(STAGE.parent, ignore_errors=True)
    shutil.copytree(SRC, STAGE, ignore=EXCLUDE)

def slim(*args):
    # slim loads this environment into a case-insensitive ConfigParser and fails when keys
    # differ only by case, such as SHELL and shell. Pass one entry per case-folded key.
    env = dict({k.lower(): (k, v) for k, v in os.environ.items()}.values())
    run(["slim", *args], check=True, env=env)

def package():
    shutil.rmtree(DIST, ignore_errors=True)
    sort_confs(SRC)
    stage()
    DIST.mkdir(parents=True, exist_ok=True)
    slim("package", str(STAGE), "-o", str(DIST))

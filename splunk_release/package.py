"""Stage and package the Splunk app."""

import os
import shutil
import subprocess
from pathlib import Path

from splunk_release.azure import run
from splunk_release.version import DIST, SRC, STAGE

# Exclude hidden files, bytecode, and tests from the package.
EXCLUDE = shutil.ignore_patterns(".*", "__pycache__", "*.pyc", "*.pyo", "tests")

def sort_meta(path):
    """Sort a .meta file: [] first, then stanzas without "/", then stanzas with "/"; keys sorted."""
    from ksconf.conf.parser import GLOBAL_STANZA, write_conf

    from splunk_release.compare import parse
    conf = parse(path)
    order = sorted(conf, key=lambda name: (name is not GLOBAL_STANZA, "/" in str(name), str(name)))
    write_conf(path, {name: dict(sorted(conf[name].items())) for name in order}, sort=False)

def sort_confs(root):
    """Sort stanzas and keys in every .conf and .meta file under root with ksconf, one blank line apart."""
    for meta in sorted(Path(root).rglob("*.meta")):
        sort_meta(meta)
    confs = sorted(str(p) for p in Path(root).rglob("*.conf"))
    if confs:
        # ksconf returns 9 when it rewrites a file.
        result = run(["ksconf", "sort", "--inplace", "--quiet", *confs], check=False)
        if result.returncode not in (0, 9):
            raise subprocess.CalledProcessError(
                result.returncode, result.args, result.stdout, result.stderr
            )

def stage():
    """Copy package/ to build/<app>; slim requires the folder and tarball root to match the app id."""
    shutil.rmtree(STAGE.parent, ignore_errors=True)
    shutil.copytree(SRC, STAGE, ignore=EXCLUDE)

def slim(*args):
    # Pass one entry per case-folded environment key.
    env = dict({k.lower(): (k, v) for k, v in os.environ.items()}.values())
    run(["slim", *args], check=True, env=env)

def package():
    shutil.rmtree(DIST, ignore_errors=True)
    sort_confs(SRC)
    stage()
    DIST.mkdir(parents=True, exist_ok=True)
    slim("package", str(STAGE), "-o", str(DIST))

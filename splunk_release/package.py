"""Stage and package the Splunk app."""

import os
import shutil
import subprocess
from pathlib import Path

from splunk_release.azure import log, run
from splunk_release.version import APP, DIST, SRC, STAGE, highest

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

INSTALL_REMOVED = ("install_source_checksum", "install_source_local_checksum", "state_change_requires_restart")


def app_conf_required(root, app):
    """Set the app.conf settings Splunk Cloud AppInspect requires, with one warning each."""
    from ksconf.conf.parser import write_conf

    from splunk_release import compare
    path = root / "default" / "app.conf"
    conf = compare.parse(path)
    versions = [conf[stanza]["version"] for stanza in ("id", "launcher") if conf.get(stanza, {}).get("version")]
    label = conf.get("ui", {}).get("label", "")
    required = {
        ("id", "name"): app,
        ("id", "version"): highest(*versions) if versions else "1.0.0",
        ("package", "id"): app,
        ("package", "check_for_updates"): "false",
        ("ui", "label"): label if 5 <= len(label) <= 80 else (app if len(app) >= 5 else f"{app} app")[:80],
    }
    required["launcher", "version"] = required["id", "version"]
    if conf.get("install", {}).get("is_configured", "").strip().lower() in ("1", "t", "true", "y", "yes", "on"):
        required["install", "is_configured"] = "false"
    changed = False
    for (stanza, key), value in required.items():
        if conf.get(stanza, {}).get(key) != value:
            conf.setdefault(stanza, {})[key] = value
            log("warning", f"default/app.conf [{stanza}] {key} = {value}: required by Splunk Cloud AppInspect")
            changed = True
    for key in INSTALL_REMOVED:
        if key in conf.get("install", {}):
            del conf["install"][key]
            log("warning", f"default/app.conf [install] {key} removed: not allowed in Splunk Cloud apps")
            changed = True
    if changed:
        write_conf(path, conf)

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
    app_conf_required(SRC, APP)
    stage()
    DIST.mkdir(parents=True, exist_ok=True)
    slim("package", str(STAGE), "-o", str(DIST))

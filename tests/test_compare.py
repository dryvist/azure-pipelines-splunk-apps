"""Tests for splunk_release.compare."""

from unittest import TestCase

import io
import tarfile
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

from _common import write_tgz
from splunk_release import compare


def check_install_checksum():
    checksum = "[app/install/install_source_checksum]\ndata = abc\n\n"
    with tempfile.TemporaryDirectory() as tmp:
        meta = Path(tmp, "metadata", "local.meta")
        meta.parent.mkdir()
        meta.write_text(checksum + "[views]\naccess = read : [*]\n")
        with redirect_stdout(io.StringIO()) as out:
            compare.drop_install_checksum(Path(tmp))
        assert "data = abc" in out.getvalue()
        assert meta.read_text() == "[views]\naccess = read : [*]\n"
        meta.write_text(checksum)
        with redirect_stdout(io.StringIO()):
            compare.drop_install_checksum(Path(tmp))
        assert not meta.exists()
        # app.conf [install] checksum keys are removed from default/ and local/.
        default_conf, local_conf = Path(tmp, "default", "app.conf"), Path(tmp, "local", "app.conf")
        default_conf.parent.mkdir()
        local_conf.parent.mkdir()
        default_conf.write_text("[install]\ninstall_source_checksum = abc\nis_configured = 1\n")
        local_conf.write_text("[install]\ninstall_source_checksum = abc\ninstall_source_local_checksum = def\n")
        with redirect_stdout(io.StringIO()) as out:
            compare.drop_install_checksum(Path(tmp))
        assert "install_source_local_checksum = def" in out.getvalue()
        assert default_conf.read_text() == "[install]\nis_configured = 1\n"
        assert not local_conf.exists()


def check_compare():
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
                "my_ta/metadata/default.meta": "[]\nexport = system\n\n[]\nowner = nobody\n",
                "my_ta/users/admin/local/savedsearches.conf": "[search]\n",
                "my_ta/lookups/same.csv": "a,b\r\n1,2\r\n",
            },
        )
        write_tgz(
            source_dir / "my_ta-1.4.10.tar.gz",
            {
                "my_ta/default/props.conf": "[changed]\nvalue = package\n",
                "my_ta/default/source-only.conf": "[source]\n",
                "my_ta/lookups/same.csv": "a,b\n1,2 \n\n",
                "my_ta/local/added.conf": "[source-local]\n",
            },
        )
        output = io.StringIO()
        with redirect_stdout(output):
            compare.tree(target_dir, source_dir, out)
            compare.local_diff(target_dir, source_dir, out)
            compare.diff(target_dir, source_dir, out)
        tree_text = (out / "my_ta-tree.txt").read_text()
        local_text = (out / "my_ta-local-vs-default.diff").read_text()
        html_text = (out / "my_ta-diff.html").read_text()
        assert "props.conf [changed] 50% (2 -> 2 lines)" in tree_text
        assert "source-only.conf [added]" in tree_text
        assert "same.csv" not in tree_text
        tree_lines = tree_text.splitlines()
        assert "local/" in tree_lines
        assert "  props.conf [removed] 5 lines" in tree_lines
        assert "  added.conf [added] 1 lines" in tree_lines
        assert "metadata/" in tree_lines
        assert "  local.meta [removed] 2 lines" in tree_lines
        assert "users/" in tree_lines
        assert "      savedsearches.conf [removed] 1 lines" in tree_lines
        assert compare.change_tree([], Path(), Path()) == "NO DIFFERENCES"
        assert compare.percent_changed([b"a"] * 200, [b"a"] * 199 + [b"b"]) == "<1%"
        assert "local/props.conf (Changed)\n" in local_text
        assert "-value = local" in local_text and "+value = package" in local_text
        assert "[new]" in local_text
        assert "my_ta deployed diff" in html_text
        assert "default/" in html_text and "props.conf [changed]" in html_text
        assert '<table class="diff"' in html_text
        assert "Local vs default" not in html_text
        assert "Added lines:" not in html_text
        assert "props.conf [changed]" in html_text
        patch_text = (out / "my_ta.patch").read_text()
        stanza_text = (out / "my_ta-stanzas.txt").read_text()
        assert "default/props.conf\n  [changed] [changed] 1 settings\n  [new] [removed] 1 settings" in stanza_text
        assert "metadata/default.meta\n  [] [removed] 2 settings" in stanza_text
        printed = output.getvalue()
        assert printed.index("Changed stanzas") < printed.index("Changed lines") < printed.index("--- target/default/props.conf")
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
        assert "## Deployed change tree" not in summary
        assert "  props.conf [changed]" not in summary
        logs = output.getvalue()
        assert logs.index("local/props.conf (Changed)") < logs.index("--- target/default/props.conf")
        assert "\n\n\n" + "=" * 100 + "\ndefault/props.conf (Changed, " in logs
        assert "--- target/default/props.conf" in logs
        assert "##[" not in patch_text
        assert "##vso[task.uploadsummary]" in logs
        assert logs.endswith(summary)
        assert "my_ta: target vs source" in logs
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
            meta = archive.extractfile("my_ta/metadata/default.meta").read().decode()
            assert "access = read : [*]" in meta
            assert "export = system" in meta and "owner = nobody" in meta


class CompareTests(TestCase):
    def test_compare(self):
        check_compare()

    def test_install_checksum(self):
        check_install_checksum()


if __name__ == "__main__":
    check_compare()
    check_install_checksum()
    print("ok")

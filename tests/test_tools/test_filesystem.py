"""Unit tests for filesystem tools."""

import tempfile
from pathlib import Path
from ai_cli.tools.filesystem.grep import grep_codebase
from ai_cli.tools.filesystem.patch import patch_file
from ai_cli.tools.filesystem.read import read_file
from ai_cli.tools.filesystem.tree import build_tree
from ai_cli.tools.filesystem.write import write_file


def test_write_and_read_file():
    """Verify writing and reading files with line numbering."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "sample.py"
        content = "line 1\nline 2\nline 3\nline 4\nline 5"

        write_res = write_file(file_path, content)
        assert write_res.created is True
        assert write_res.bytes_written == len(content.encode("utf-8"))

        # Read entire file
        read_res = read_file(file_path)
        assert read_res.total_lines == 5
        assert "1 | line 1" in read_res.content

        # Read line range
        read_slice = read_file(file_path, start_line=2, end_line=3)
        assert read_slice.start_line == 2
        assert read_slice.end_line == 3
        assert "line 2" in read_slice.content
        assert "line 3" in read_slice.content
        assert "line 1" not in read_slice.content


def test_patch_file():
    """Verify precision search-and-replace and diff generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "code.py"
        file_path.write_text("def hello():\n    return 'old'\n")

        target = "    return 'old'"
        replacement = "    return 'new'"

        patch_res = patch_file(file_path, target, replacement)
        assert patch_res.success is True
        assert "-    return 'old'" in patch_res.diff
        assert "+    return 'new'" in patch_res.diff

        # Check modified file
        updated = file_path.read_text()
        assert "return 'new'" in updated


def test_tree_and_grep():
    """Verify tree formatting and regex pattern search."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        sub = tmp_path / "pkg"
        sub.mkdir()
        (sub / "mod.py").write_text("SECRET_KEY = '12345'\ndef authenticate(): pass")

        tree_str = build_tree(tmp_path)
        assert "pkg/" in tree_str
        assert "mod.py" in tree_str

        grep_res = grep_codebase("SECRET_KEY", root_dir=tmp_path)
        assert grep_res.total_matches == 1
        assert grep_res.matches[0].line_number == 1
        assert "SECRET_KEY" in grep_res.matches[0].line_content

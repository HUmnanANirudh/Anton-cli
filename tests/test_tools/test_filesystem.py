"""Unit tests for filesystem tools."""

import tempfile
from pathlib import Path
from ai_cli.tools.filesystem.grep import grep_codebase
from ai_cli.tools.filesystem.nav import (
    change_working_dir,
    get_current_working_dir,
    get_system_context,
)
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


def test_navigation_and_system_context():
    """Verify get_current_working_dir, change_working_dir, and get_system_context."""
    original_cwd = get_current_working_dir()
    assert Path(original_cwd).exists()

    with tempfile.TemporaryDirectory() as tmp_dir:
        res = change_working_dir(tmp_dir)
        assert "Successfully changed" in res
        assert get_current_working_dir() == str(Path(tmp_dir).resolve())

        # Test desktop/home shortcuts
        home_res = change_working_dir("home")
        assert "Successfully changed" in home_res
        assert get_current_working_dir() == str(Path.home().resolve())

        # Test invalid directory
        err_res = change_working_dir("/non_existent_dir_123456789")
        assert "does not exist" in err_res

        # Test system context output
        ctx_info = get_system_context()
        assert "Working Directory:" in ctx_info
        assert "Operating System:" in ctx_info
        assert "Python Version:" in ctx_info

    # Restore original working dir
    change_working_dir(original_cwd)
    assert get_current_working_dir() == original_cwd


def test_full_device_filesystem_access():
    """Verify read, write, patch, and tree access across arbitrary device locations."""
    with tempfile.TemporaryDirectory() as outside_dir:
        outside_path = Path(outside_dir) / "test_doc.txt"

        # Write outside CWD
        w_res = write_file(outside_path, "Hello device-wide access!\nSecond line.")
        assert w_res.created is True
        assert outside_path.exists()

        # Read outside CWD
        r_res = read_file(outside_path)
        assert "Hello device-wide access!" in r_res.content

        # Patch outside CWD
        p_res = patch_file(outside_path, "Hello device-wide access!", "Hello from anywhere!")
        assert p_res.success is True
        assert "Hello from anywhere!" in outside_path.read_text()

        # Tree outside CWD
        t_res = build_tree(outside_dir)
        assert "test_doc.txt" in t_res


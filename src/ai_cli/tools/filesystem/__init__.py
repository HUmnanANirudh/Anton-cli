"""Filesystem tools package."""

from ai_cli.tools.filesystem.grep import GrepMatch, GrepResult, grep_codebase
from ai_cli.tools.filesystem.patch import PatchResult, generate_diff, patch_file
from ai_cli.tools.filesystem.read import FileReadResult, read_file
from ai_cli.tools.filesystem.tree import build_tree
from ai_cli.tools.filesystem.write import FileWriteResult, write_file

__all__ = [
    "read_file",
    "FileReadResult",
    "write_file",
    "FileWriteResult",
    "patch_file",
    "PatchResult",
    "generate_diff",
    "build_tree",
    "grep_codebase",
    "GrepMatch",
    "GrepResult",
]

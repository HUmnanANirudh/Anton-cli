"""Filesystem patch tool for targeted search-and-replace edits."""

import difflib
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from ai_cli.config.settings import get_settings


class PatchResult(BaseModel):
    """Result of applying a patch to a file."""

    file_path: str
    success: bool
    diff: str
    error: Optional[str] = None


def generate_diff(original_text: str, modified_text: str, file_path: str) -> str:
    """Generate a unified diff representation between two texts."""
    orig_lines = original_text.splitlines(keepends=True)
    mod_lines = modified_text.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )
    return "".join(diff)


from ai_cli.tools.filesystem.nav import resolve_target_path


def patch_file(
    file_path: str | Path,
    target_content: str,
    replacement_content: str,
    allow_multiple: bool = False,
) -> PatchResult:
    """
    Replace a precise block of text (`target_content`) with `replacement_content` in a file anywhere on device.
    Returns the unified diff preview.
    """
    path = resolve_target_path(file_path)

    if not path.exists():
        return PatchResult(
            file_path=str(file_path),
            success=False,
            diff="",
            error=f"File not found: {file_path}",
        )

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return PatchResult(
            file_path=str(file_path),
            success=False,
            diff="",
            error=f"Error reading file: {e}",
        )

    count = content.count(target_content)
    if count == 0:
        return PatchResult(
            file_path=str(file_path),
            success=False,
            diff="",
            error="Target content was not found in the file. Ensure exact whitespace and line match.",
        )

    if count > 1 and not allow_multiple:
        return PatchResult(
            file_path=str(file_path),
            success=False,
            diff="",
            error=f"Target content was found {count} times in the file. Provide a more specific surrounding context.",
        )

    if allow_multiple:
        new_content = content.replace(target_content, replacement_content)
    else:
        new_content = content.replace(target_content, replacement_content, 1)

    diff = generate_diff(content, new_content, str(file_path))

    try:
        path.write_text(new_content, encoding="utf-8")
        return PatchResult(
            file_path=str(file_path),
            success=True,
            diff=diff,
        )
    except Exception as e:
        return PatchResult(
            file_path=str(file_path),
            success=False,
            diff="",
            error=f"Error writing patched file: {e}",
        )

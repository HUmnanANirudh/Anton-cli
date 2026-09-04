"""Filesystem read tool."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from ai_cli.config.settings import get_settings


class FileReadResult(BaseModel):
    """Result from reading a file."""

    file_path: str
    content: str
    total_lines: int
    start_line: int
    end_line: int
    truncated: bool = False
    error: Optional[str] = None


from ai_cli.tools.filesystem.nav import resolve_target_path


def read_file(
    file_path: str | Path,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    with_line_numbers: bool = True,
) -> FileReadResult:
    """
    Read contents of a file with optional line-range slicing and formatting.
    Supports reading files from anywhere on the device.
    """
    path = resolve_target_path(file_path)

    if not path.exists():
        return FileReadResult(
            file_path=str(file_path),
            content="",
            total_lines=0,
            start_line=0,
            end_line=0,
            error=f"File not found: {file_path}",
        )

    if not path.is_file():
        return FileReadResult(
            file_path=str(file_path),
            content="",
            total_lines=0,
            start_line=0,
            end_line=0,
            error=f"Path is not a regular file: {file_path}",
        )

    try:
        raw_content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return FileReadResult(
            file_path=str(file_path),
            content="",
            total_lines=0,
            start_line=0,
            end_line=0,
            error=f"Failed to read file: {e}",
        )

    lines = raw_content.splitlines()
    total_lines = len(lines)

    s_line = max(1, start_line or 1)
    e_line = min(total_lines, end_line or total_lines) if total_lines > 0 else 0

    if total_lines == 0:
        return FileReadResult(
            file_path=str(file_path),
            content="(empty file)",
            total_lines=0,
            start_line=0,
            end_line=0,
        )

    sliced_lines = lines[s_line - 1 : e_line]

    if with_line_numbers:
        formatted_lines = [f"{s_line + i:4d} | {line}" for i, line in enumerate(sliced_lines)]
        formatted_content = "\n".join(formatted_lines)
    else:
        formatted_content = "\n".join(sliced_lines)

    return FileReadResult(
        file_path=str(file_path),
        content=formatted_content,
        total_lines=total_lines,
        start_line=s_line,
        end_line=e_line,
    )

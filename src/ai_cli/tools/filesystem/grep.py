"""Codebase grep and pattern search tool."""

import os
import re
from pathlib import Path
from typing import List, Optional, Set
from pydantic import BaseModel
from ai_cli.config.settings import get_settings
from ai_cli.tools.filesystem.tree import DEFAULT_IGNORE


class GrepMatch(BaseModel):
    """Single grep pattern match."""

    file_path: str
    line_number: int
    line_content: str


class GrepResult(BaseModel):
    """Result of searching pattern across files."""

    query: str
    total_matches: int
    matches: List[GrepMatch]
    error: Optional[str] = None


def grep_codebase(
    query: str,
    root_dir: Optional[str | Path] = None,
    is_regex: bool = False,
    case_sensitive: bool = False,
    max_matches: int = 50,
) -> GrepResult:
    """Search for string or regex pattern across workspace files."""
    settings = get_settings()
    base_path = Path(root_dir) if root_dir else settings.BASE_DIR
    if not base_path.is_absolute():
        base_path = settings.BASE_DIR / base_path

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags) if is_regex else re.compile(re.escape(query), flags)
    except re.error as e:
        return GrepResult(query=query, total_matches=0, matches=[], error=f"Invalid regex: {e}")

    matches: List[GrepMatch] = []

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE and not d.startswith(".")]

        for file in files:
            if file.startswith("."):
                continue
            file_path = Path(root) / file
            rel_path = str(file_path.relative_to(base_path))

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for i, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    matches.append(
                        GrepMatch(
                            file_path=rel_path,
                            line_number=i,
                            line_content=line.strip()[:200],
                        )
                    )
                    if len(matches) >= max_matches:
                        return GrepResult(
                            query=query,
                            total_matches=len(matches),
                            matches=matches,
                        )

    return GrepResult(
        query=query,
        total_matches=len(matches),
        matches=matches,
    )

"""Directory tree generation tool."""

import os
from pathlib import Path
from typing import List, Optional, Set
from ai_cli.config.settings import get_settings


DEFAULT_IGNORE: Set[str] = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
    "data",
    ".idea",
    ".vscode",
    ".anton",
}


def build_tree(
    root_dir: Optional[str | Path] = None,
    max_depth: int = 3,
    custom_ignore: Optional[Set[str]] = None,
) -> str:
    """Generate an ASCII visual representation of directory structure."""
    settings = get_settings()
    base_path = Path(root_dir) if root_dir else settings.BASE_DIR
    if not base_path.is_absolute():
        base_path = settings.BASE_DIR / base_path

    if not base_path.exists() or not base_path.is_dir():
        return f"Directory not found: {base_path}"

    ignore_set = set(DEFAULT_IGNORE)
    if custom_ignore:
        ignore_set.update(custom_ignore)

    lines: List[str] = [f"{base_path.name}/"]

    def _walk(current_dir: Path, prefix: str = "", current_depth: int = 1):
        if current_depth > max_depth:
            return

        try:
            entries = sorted(list(current_dir.iterdir()), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in ignore_set and not e.name.startswith(".")]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                _walk(entry, prefix + child_prefix, current_depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    _walk(base_path)
    return "\n".join(lines)

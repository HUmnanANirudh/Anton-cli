"""Directory navigation and system inspection tools."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional
from ai_cli.config.settings import get_settings


def resolve_target_path(path_input: str | Path, base_dir: Optional[Path] = None) -> Path:
    """
    Resolve any file or directory path across the entire device.
    Supports '~', environment variables ($HOME, $USER), relative paths, and user folder shortcuts.
    """
    if not path_input:
        return (base_dir or Path.cwd()).resolve()

    raw = str(path_input).strip().strip("'\"")
    # Strip suffixes like ' directory' or ' folder'
    for suffix in [" directory", " folder"]:
        if raw.lower().endswith(suffix):
            raw = raw[:-len(suffix)].strip()

    expanded = os.path.expandvars(os.path.expanduser(raw))
    path = Path(expanded)

    if path.is_absolute():
        return path.resolve()

    root = base_dir or get_settings().BASE_DIR or Path.cwd()
    candidate = (root / path).resolve()
    if candidate.exists():
        return candidate

    # Check home shortcuts (e.g. 'Desktop', 'Downloads', 'Documents', 'Pictures')
    home = Path.home()
    if raw.lower() == "home":
        return home.resolve()
    if (home / raw).exists():
        return (home / raw).resolve()
    if (home / raw.capitalize()).exists():
        return (home / raw.capitalize()).resolve()
    if (home / raw.title()).exists():
        return (home / raw.title()).resolve()

    return candidate


def get_current_working_dir() -> str:
    """Get the current absolute working directory."""
    return str(Path.cwd().resolve())


def change_working_dir(target_dir: str) -> str:
    """
    Change the current working directory anywhere on the device.
    Expands '~', relative paths, environment variables, and well-known user folders.
    """
    try:
        path = resolve_target_path(target_dir)

        if not path.exists():
            return f"Error: Directory '{target_dir}' does not exist ({path})."
        if not path.is_dir():
            return f"Error: Path '{target_dir}' is a file, not a directory."

        os.chdir(str(path))
        settings = get_settings()
        settings.BASE_DIR = path

        return f"Successfully changed working directory to: {path}"
    except Exception as e:
        return f"Failed to change directory to '{target_dir}': {e}"


def get_system_context() -> str:
    """
    Get information about the current environment: user, OS, machine, working directory.
    """
    cwd = Path.cwd().resolve()
    user = os.getenv("USER") or os.getenv("USERNAME") or "user"
    os_name = platform.system()
    os_release = platform.release()
    machine = platform.machine()
    python_ver = platform.python_version()

    # Check git branch if available
    git_branch = None
    git_head = cwd / ".git" / "HEAD"
    if git_head.exists():
        try:
            head_content = git_head.read_text(encoding="utf-8").strip()
            if head_content.startswith("ref: refs/heads/"):
                git_branch = head_content.replace("ref: refs/heads/", "")
        except Exception:
            pass

    info_lines = [
        f"User: {user}",
        f"Working Directory: {cwd}",
        f"Operating System: {os_name} {os_release} ({machine})",
        f"Python Version: {python_ver}",
    ]
    if git_branch:
        info_lines.append(f"Git Branch: {git_branch}")

    return "\n".join(info_lines)

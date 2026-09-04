"""Directory navigation and system inspection tools."""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional
from ai_cli.config.settings import get_settings


def get_current_working_dir() -> str:
    """Get the current absolute working directory."""
    return str(Path.cwd().resolve())


def change_working_dir(target_dir: str) -> str:
    """
    Change the current working directory.
    Expands '~', relative paths, environment variables, and well-known user folders (e.g. 'desktop', 'downloads', 'home').
    """
    try:
        clean_target = target_dir.strip().strip("'\"")
        # Remove trailing words like "directory" or "folder" if user passed "desktop directory"
        for suffix in [" directory", " folder"]:
            if clean_target.lower().endswith(suffix):
                clean_target = clean_target[:-len(suffix)].strip()

        raw_path = os.path.expandvars(os.path.expanduser(clean_target))
        path = Path(raw_path).resolve()

        if not path.exists():
            home = Path.home()
            if clean_target.lower() == "home":
                path = home
            elif (home / clean_target).is_dir():
                path = (home / clean_target).resolve()
            elif (home / clean_target.capitalize()).is_dir():
                path = (home / clean_target.capitalize()).resolve()
            elif (home / clean_target.title()).is_dir():
                path = (home / clean_target.title()).resolve()

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

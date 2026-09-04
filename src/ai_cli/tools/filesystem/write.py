"""Filesystem write tool."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from ai_cli.config.settings import get_settings


class FileWriteResult(BaseModel):
    """Result from writing to a file."""

    file_path: str
    bytes_written: int
    created: bool
    error: Optional[str] = None


def write_file(
    file_path: str | Path,
    content: str,
    overwrite: bool = True,
) -> FileWriteResult:
    """
    Create a new file or overwrite an existing file with the provided content.
    """
    settings = get_settings()
    path = Path(file_path)
    if not path.is_absolute():
        path = settings.BASE_DIR / path

    existed = path.exists()
    if existed and not overwrite:
        return FileWriteResult(
            file_path=str(file_path),
            bytes_written=0,
            created=False,
            error=f"File already exists and overwrite is set to False: {file_path}",
        )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        bytes_written = len(content.encode("utf-8"))
        return FileWriteResult(
            file_path=str(file_path),
            bytes_written=bytes_written,
            created=not existed,
        )
    except Exception as e:
        return FileWriteResult(
            file_path=str(file_path),
            bytes_written=0,
            created=False,
            error=f"Failed to write file: {e}",
        )

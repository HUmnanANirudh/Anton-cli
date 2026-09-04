"""Codebase indexer and document chunker for ChromaDB."""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from ai_cli.memory.chroma import ChromaMemory
from ai_cli.memory.embeddings import LocalEmbeddings, get_embeddings


IGNORE_DIRS: Set[str] = {
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

SUPPORTED_EXTENSIONS: Set[str] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".txt",
    ".html",
    ".css",
    ".sh",
    ".sql",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
}


def compute_file_hash(content: str) -> str:
    """Compute SHA256 hex digest of file text."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class CodeChunk:
    """Represents a chunk of indexed code/text."""

    def __init__(
        self,
        chunk_id: str,
        file_path: str,
        content: str,
        start_line: int,
        end_line: int,
        file_hash: str,
    ):
        self.chunk_id = chunk_id
        self.file_path = file_path
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.file_hash = file_hash

    def to_metadata(self) -> Dict[str, str | int]:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "file_hash": self.file_hash,
        }


class CodeIndexer:
    """Indexes source code and project files into ChromaDB with incremental hash caching."""

    def __init__(
        self,
        chroma_memory: Optional[ChromaMemory] = None,
        embeddings: Optional[LocalEmbeddings] = None,
        chunk_size_lines: int = 50,
        chunk_overlap_lines: int = 10,
    ):
        self.memory = chroma_memory or ChromaMemory()
        self.embeddings = embeddings or get_embeddings()
        self.chunk_size_lines = chunk_size_lines
        self.chunk_overlap_lines = chunk_overlap_lines

    def chunk_file(self, file_path: Path, root_path: Path) -> List[CodeChunk]:
        """Split a file into line-aware chunks with metadata."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        if not content.strip():
            return []

        rel_path = str(file_path.relative_to(root_path))
        file_hash = compute_file_hash(content)
        lines = content.splitlines()
        chunks: List[CodeChunk] = []

        if len(lines) <= self.chunk_size_lines:
            chunk_id = f"{rel_path}:1-{len(lines)}"
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    content=content,
                    start_line=1,
                    end_line=len(lines),
                    file_hash=file_hash,
                )
            )
            return chunks

        start = 0
        while start < len(lines):
            end = min(start + self.chunk_size_lines, len(lines))
            chunk_content = "\n".join(lines[start:end])
            start_line = start + 1
            end_line = end
            chunk_id = f"{rel_path}:{start_line}-{end_line}"

            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    content=chunk_content,
                    start_line=start_line,
                    end_line=end_line,
                    file_hash=file_hash,
                )
            )

            if end >= len(lines):
                break
            start += self.chunk_size_lines - self.chunk_overlap_lines

        return chunks

    def scan_directory(self, root_dir: Path) -> List[Path]:
        """Discover all supported source files, ignoring excluded directories."""
        valid_files: List[Path] = []
        for root, dirs, files in os.walk(root_dir):
            # Prune ignored directories in place
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    valid_files.append(Path(root) / file)

        return valid_files

    def index_workspace(
        self,
        workspace_dir: Path | str,
        collection_name: str = ChromaMemory.DEFAULT_COLLECTION,
        force_reindex: bool = False,
    ) -> Dict[str, int]:
        """Index or incrementally update workspace files into ChromaDB."""
        root = Path(workspace_dir).resolve()
        existing_hashes = {} if force_reindex else self.memory.get_file_hashes(collection_name)
        discovered_files = self.scan_directory(root)

        indexed_files = 0
        skipped_files = 0
        total_chunks = 0

        for file_path in discovered_files:
            rel_path = str(file_path.relative_to(root))
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                current_hash = compute_file_hash(content)
            except Exception:
                continue

            # Check if file has changed
            if not force_reindex and existing_hashes.get(rel_path) == current_hash:
                skipped_files += 1
                continue

            # If modified or new, delete old chunks first
            self.memory.delete_by_file(collection_name, rel_path)

            # Generate chunks
            chunks = self.chunk_file(file_path, root)
            if not chunks:
                continue

            chunk_ids = [c.chunk_id for c in chunks]
            chunk_docs = [f"File: {c.file_path} (Lines {c.start_line}-{c.end_line})\n\n{c.content}" for c in chunks]
            chunk_metas = [c.to_metadata() for c in chunks]

            # Compute embeddings and upsert
            embeddings = self.embeddings.embed_documents(chunk_docs)
            self.memory.upsert(
                collection_name=collection_name,
                ids=chunk_ids,
                documents=chunk_docs,
                embeddings=embeddings,
                metadatas=chunk_metas,
            )

            indexed_files += 1
            total_chunks += len(chunks)

        return {
            "indexed_files": indexed_files,
            "skipped_files": skipped_files,
            "total_chunks_added": total_chunks,
        }

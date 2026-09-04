"""Application settings and configuration management."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Anton CLI Configuration Settings."""

    # Application details
    APP_NAME: str = "Anton CLI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path.cwd())
    DATA_DIR: Path = Field(default_factory=lambda: Path.cwd() / "data")
    CHROMA_PERSIST_DIR: str = "data/chroma"

    # Groq API Configuration (Primary LLM & Multi-Agent Evaluations)
    GROQ_API_KEY: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", validation_alias="GROQ_MODEL")
    GROQ_EVAL_MODEL: str = Field(default="llama-3.3-70b-versatile", validation_alias="GROQ_EVAL_MODEL")

    # Tavily Search API Configuration (Primary Web Search)
    TAVILY_API_KEY: Optional[str] = Field(default=None, validation_alias="TAVILY_API_KEY")

    # Google Custom Search API Configuration (Secondary / Fallback)
    GOOGLE_API_KEY: Optional[str] = Field(default=None, validation_alias="GOOGLE_API_KEY")
    GOOGLE_CSE_ID: Optional[str] = Field(default=None, validation_alias="GOOGLE_CSE_ID")

    # Embeddings Configuration
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5", validation_alias="EMBEDDING_MODEL")

    # Guardrails & Safety
    ENABLE_INPUT_GUARDRAILS: bool = True
    ENABLE_OUTPUT_GUARDRAILS: bool = True
    ENABLE_EXECUTION_GUARDRAILS: bool = True
    AUTO_APPROVE_COMMANDS: bool = False

    # Execution limits
    SHELL_TIMEOUT_SECONDS: int = 60
    MAX_SEARCH_RESULTS: int = 5
    MAX_FILE_READ_BYTES: int = 1_000_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def chroma_full_path(self) -> Path:
        """Get absolute path for ChromaDB storage directory."""
        path = Path(self.CHROMA_PERSIST_DIR)
        if not path.is_absolute():
            path = self.BASE_DIR / path
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()

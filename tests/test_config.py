"""Tests for Anton CLI configuration and settings."""

from pathlib import Path
from ai_cli.config.settings import Settings, get_settings


def test_default_settings():
    """Verify default settings initialization."""
    settings = Settings()
    assert settings.APP_NAME == "Anton CLI"
    assert settings.APP_VERSION == "0.1"
    assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    assert settings.CHROMA_PERSIST_DIR == "data/chroma"
    assert settings.ENABLE_INPUT_GUARDRAILS is True
    assert settings.ENABLE_OUTPUT_GUARDRAILS is True
    assert settings.ENABLE_EXECUTION_GUARDRAILS is True
    assert settings.AUTO_APPROVE_COMMANDS is False


def test_chroma_full_path():
    """Verify absolute path resolution for chroma persistence dir."""
    settings = Settings(BASE_DIR=Path("/custom/base"), CHROMA_PERSIST_DIR="data/chroma")
    assert settings.chroma_full_path == Path("/custom/base/data/chroma")


def test_singleton_get_settings():
    """Verify singleton caching behavior."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

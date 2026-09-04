"""Unit tests for Groq provider and factory."""

import pytest
from ai_cli.providers.factory import ProviderFactory
from ai_cli.providers.groq import GroqProvider


def test_provider_factory_resolution():
    """Verify provider factory returns configured Groq provider."""
    provider = ProviderFactory.get_provider("groq")
    assert isinstance(provider, GroqProvider)

    with pytest.raises(ValueError, match="Unsupported provider"):
        ProviderFactory.get_provider("unknown_provider")


def test_groq_provider_credential_validation():
    """Verify credentials check behavior."""
    p_valid = GroqProvider(api_key="gsk_test123456789012345678901234567890")
    assert p_valid.validate_credentials() is True

    p_invalid = GroqProvider(api_key="")
    assert p_invalid.validate_credentials() is False

    with pytest.raises(ValueError, match="GROQ_API_KEY is not configured"):
        p_invalid.get_chat_model()


def test_groq_model_instantiation():
    """Verify ChatGroq model creation with custom arguments."""
    provider = GroqProvider(api_key="gsk_test123456789012345678901234567890")
    chat_model = provider.get_chat_model(model_name="llama-3.1-8b-instant", temperature=0.7)
    
    assert chat_model.model_name == "llama-3.1-8b-instant"
    assert chat_model.temperature == 0.7

    eval_model = provider.get_eval_model()
    assert eval_model.temperature == 0.0

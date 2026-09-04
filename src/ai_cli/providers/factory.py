"""LLM Provider Factory."""

from typing import Dict, Type
from ai_cli.providers.base import BaseLLMProvider
from ai_cli.providers.groq import GroqProvider


class ProviderFactory:
    """Factory for resolving and instantiating LLM providers."""

    _PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
        "groq": GroqProvider,
    }

    @classmethod
    def get_provider(cls, name: str = "groq") -> BaseLLMProvider:
        """Get provider instance by name."""
        provider_cls = cls._PROVIDERS.get(name.lower())
        if not provider_cls:
            raise ValueError(
                f"Unsupported provider '{name}'. Available providers: {list(cls._PROVIDERS.keys())}"
            )
        return provider_cls()

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseLLMProvider]) -> None:
        """Register a new LLM provider class."""
        cls._PROVIDERS[name.lower()] = provider_cls

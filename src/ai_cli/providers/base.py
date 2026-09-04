"""Base abstract LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Anton CLI."""

    @abstractmethod
    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Instantiate and return a LangChain chat model."""
        pass

    @abstractmethod
    def get_eval_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Instantiate and return a deterministic model for multi-agent evaluations."""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if required API credentials exist."""
        pass

"""Groq LLM provider implementation using langchain-groq."""

from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from ai_cli.config.settings import get_settings
from ai_cli.providers.base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    """Primary LLM provider utilizing ultra-fast Groq API."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GROQ_API_KEY
        self.default_model = settings.GROQ_MODEL
        self.default_eval_model = settings.GROQ_EVAL_MODEL

    def validate_credentials(self) -> bool:
        """Check if Groq API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Instantiate Groq Chat Model for agent reasoning."""
        if not self.validate_credentials():
            raise ValueError(
                "GROQ_API_KEY is not configured. Please set it in your .env file."
            )

        model = model_name or self.default_model
        return ChatGroq(
            groq_api_key=self.api_key,
            model_name=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def get_eval_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Instantiate deterministic Groq Chat Model for multi-agent evaluations."""
        if not self.validate_credentials():
            raise ValueError(
                "GROQ_API_KEY is not configured. Please set it in your .env file."
            )

        model = model_name or self.default_eval_model
        return ChatGroq(
            groq_api_key=self.api_key,
            model_name=model,
            temperature=temperature,
            **kwargs,
        )

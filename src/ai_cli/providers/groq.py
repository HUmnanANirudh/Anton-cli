"""Groq LLM provider implementation with dynamic model switching and registry."""

from typing import Any, Dict, List, Optional
import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from ai_cli.config.settings import get_settings
from ai_cli.providers.base import BaseLLMProvider

# Curated registry of supported Groq production and preview models
SUPPORTED_GROQ_MODELS: List[Dict[str, str]] = [
    {
        "id": "openai/gpt-oss-20b",
        "name": "OpenAI GPT-OSS 20B",
        "speed": "1000 t/s",
        "context": "131k",
        "type": "Production (Default)",
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile",
        "speed": "280 t/s",
        "context": "131k",
        "type": "Production",
    },
    {
        "id": "llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "speed": "560 t/s",
        "context": "131k",
        "type": "Production (Fast)",
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "OpenAI GPT-OSS 120B",
        "speed": "500 t/s",
        "context": "131k",
        "type": "Production",
    },
    {
        "id": "groq/compound",
        "name": "Groq Compound System",
        "speed": "450 t/s",
        "context": "131k",
        "type": "Production System",
    },
    {
        "id": "groq/compound-mini",
        "name": "Groq Compound Mini",
        "speed": "450 t/s",
        "context": "131k",
        "type": "Production System",
    },
    {
        "id": "qwen/qwen3.6-27b",
        "name": "Qwen 3.6 27B",
        "speed": "500 t/s",
        "context": "131k",
        "type": "Preview",
    },
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B",
        "speed": "450 t/s",
        "context": "131k",
        "type": "Preview",
    },
    {
        "id": "minimaxai/minimax-m2.7",
        "name": "MiniMax M2.7",
        "speed": "260 t/s",
        "context": "196k",
        "type": "Enterprise Preview",
    },
    {
        "id": "deepseek-r1-distill-llama-70b",
        "name": "DeepSeek R1 Distill 70B",
        "speed": "280 t/s",
        "context": "131k",
        "type": "Reasoning",
    },
]


async def fetch_live_groq_models(api_key: str) -> List[str]:
    """Fetch live list of model IDs from GroqCloud API."""
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("id") for m in data.get("data", []) if m.get("id")]
    except Exception:
        pass
    return [m["id"] for m in SUPPORTED_GROQ_MODELS]


class GroqProvider(BaseLLMProvider):
    """Primary LLM provider utilizing Groq API with dynamic model switching."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GROQ_API_KEY
        self.active_model = settings.GROQ_MODEL
        self.default_eval_model = settings.GROQ_EVAL_MODEL

    def set_active_model(self, model_id: str) -> None:
        """Switch the current active model."""
        self.active_model = model_id.strip()

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

        model = model_name or self.active_model
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

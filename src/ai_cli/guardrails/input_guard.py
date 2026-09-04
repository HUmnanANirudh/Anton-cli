"""Input guardrails for prompt injection, jailbreaks, and credential protection."""

import re
from typing import List
from pydantic import BaseModel
from ai_cli.config.settings import get_settings


class InputGuardResult(BaseModel):
    """Result of analyzing and sanitizing user input."""

    is_safe: bool
    sanitized_text: str
    flagged_reasons: List[str]
    has_jailbreak_attempt: bool


# Common prompt injection and jailbreak signatures
INJECTION_PATTERNS = [
    (r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts|rules)", "Prompt override / ignore instructions"),
    (r"(?i)disregard\s+(all\s+)?(previous|prior|system)\s+prompts?", "Prompt override / disregard instructions"),
    (r"(?i)you\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode|jailbroken)", "Persona / Jailbreak mode invocation"),
    (r"(?i)reveal\s+(your\s+)?(master|system|hidden|internal)\s+(prompt|instructions|rules)", "Direct system prompt extraction attempt"),
    (r"(?i)print\s+(the\s+)?(initial|system)\s+(prompt|instructions)", "Direct system prompt extraction attempt"),
    (r"(?i)output\s+(everything|all\s+text)\s+above", "Context boundary extraction attempt"),
]

# Sensitive credentials to detect and redact in input
CREDENTIAL_PATTERNS = [
    (r"\bgsk_[A-Za-z0-9_-]{30,}\b", "[REDACTED_GROQ_API_KEY]"),
    (r"\btvly-[A-Za-z0-9_-]{20,}\b", "[REDACTED_TAVILY_API_KEY]"),
    (r"\bsk-[A-Za-z0-9_-]{20,}\b", "[REDACTED_OPENAI_API_KEY]"),
    (r"\bAIza[0-9A-Za-z-_]{35}\b", "[REDACTED_GOOGLE_API_KEY]"),
    (r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA )?PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
]


def evaluate_input(text: str) -> InputGuardResult:
    """Analyze and sanitize user input against security policies."""
    settings = get_settings()
    if not settings.ENABLE_INPUT_GUARDRAILS:
        return InputGuardResult(
            is_safe=True,
            sanitized_text=text,
            flagged_reasons=[],
            has_jailbreak_attempt=False,
        )

    flagged_reasons: List[str] = []
    has_jailbreak = False

    # 1. Check for prompt injection / jailbreak patterns
    for pattern, reason in INJECTION_PATTERNS:
        if re.search(pattern, text):
            flagged_reasons.append(reason)
            has_jailbreak = True

    # 2. Redact accidental credential pasting
    sanitized = text
    for pattern, replacement in CREDENTIAL_PATTERNS:
        if re.search(pattern, sanitized):
            flagged_reasons.append("Pasted sensitive API key or credential was redacted")
            sanitized = re.sub(pattern, replacement, sanitized)

    is_safe = not has_jailbreak

    return InputGuardResult(
        is_safe=is_safe,
        sanitized_text=sanitized,
        flagged_reasons=flagged_reasons,
        has_jailbreak_attempt=has_jailbreak,
    )

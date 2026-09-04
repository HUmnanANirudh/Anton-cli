"""Output guardrails for system prompt defense and sensitive data redaction."""

import re
from typing import List, Set
from pydantic import BaseModel
from ai_cli.config.settings import get_settings
from ai_cli.guardrails.input_guard import CREDENTIAL_PATTERNS

# Secret canary token to ensure internal system instructions never leak
SYSTEM_CANARY_TOKEN = "ANTON_SYS_PROMPT_CANARY_49a8f2"

# Phrases indicating system prompt leakage
LEAKAGE_INDICATORS = [
    r"(?i)my\s+(system\s+prompt|master\s+prompt|initial\s+instructions)\s+(is|are|states):",
    r"(?i)here\s+(is|are)\s+the\s+(system\s+prompt|master\s+prompt|hidden\s+rules)",
    r"(?i)<SYSTEM_INSTRUCTIONS>",
    r"(?i)ANTON_SYS_PROMPT_CANARY",
]


class OutputGuardResult(BaseModel):
    """Result of analyzing and sanitizing LLM output."""

    is_safe: bool
    sanitized_output: str
    blocked_prompt_leak: bool
    redacted_secrets: List[str]


def evaluate_output(
    output_text: str,
    custom_canaries: Set[str] | None = None,
) -> OutputGuardResult:
    """
    Evaluate agent output for system prompt leakage, secret leaks, and safety.
    """
    settings = get_settings()
    if not settings.ENABLE_OUTPUT_GUARDRAILS:
        return OutputGuardResult(
            is_safe=True,
            sanitized_output=output_text,
            blocked_prompt_leak=False,
            redacted_secrets=[],
        )

    # 1. Check for Canary Token
    canary_detected = SYSTEM_CANARY_TOKEN in output_text
    if custom_canaries:
        for canary in custom_canaries:
            if canary in output_text:
                canary_detected = True
                break

    # 2. Check for structural prompt leak phrases
    leak_detected = canary_detected
    if not leak_detected:
        for pattern in LEAKAGE_INDICATORS:
            if re.search(pattern, output_text):
                leak_detected = True
                break

    if leak_detected:
        return OutputGuardResult(
            is_safe=False,
            sanitized_output=(
                "I am unable to reveal my internal system prompt or private instructions. "
                "How can I help you with your coding or technical task instead?"
            ),
            blocked_prompt_leak=True,
            redacted_secrets=[],
        )

    # 3. Redact credentials/secrets from output
    sanitized = output_text
    redacted: List[str] = []
    for pattern, replacement in CREDENTIAL_PATTERNS:
        if re.search(pattern, sanitized):
            redacted.append(replacement)
            sanitized = re.sub(pattern, replacement, sanitized)

    return OutputGuardResult(
        is_safe=True,
        sanitized_output=sanitized,
        blocked_prompt_leak=False,
        redacted_secrets=redacted,
    )

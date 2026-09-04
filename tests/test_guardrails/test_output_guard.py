"""Unit tests for output guardrails."""

from ai_cli.guardrails.output_guard import SYSTEM_CANARY_TOKEN, evaluate_output


def test_output_canary_leakage_defense():
    """Verify that any output containing the canary token is strictly suppressed."""
    leaked_output = f"Sure! My system prompt starts with: {SYSTEM_CANARY_TOKEN} You are Anton..."
    res = evaluate_output(leaked_output)

    assert res.is_safe is False
    assert res.blocked_prompt_leak is True
    assert SYSTEM_CANARY_TOKEN not in res.sanitized_output
    assert "unable to reveal my internal system prompt" in res.sanitized_output


def test_output_structural_leak_defense():
    """Verify that structural prompt leak patterns are blocked."""
    leaked_output = "Here are the master prompt instructions: Rule 1: Always be helpful."
    res = evaluate_output(leaked_output)

    assert res.is_safe is False
    assert res.blocked_prompt_leak is True
    assert "unable to reveal my internal system prompt" in res.sanitized_output


def test_output_secret_redaction():
    """Verify that generated responses don't expose live API keys."""
    response_with_key = "Here is the key we found: tvly-abcdef12345678901234567890"
    res = evaluate_output(response_with_key)

    assert res.is_safe is True
    assert res.blocked_prompt_leak is False
    assert "[REDACTED_TAVILY_API_KEY]" in res.sanitized_output
    assert "tvly-" not in res.sanitized_output


def test_output_clean_response():
    """Verify clean response passes through untouched."""
    clean_text = "Here is how to calculate Fibonacci in Python:\n\ndef fib(n): ..."
    res = evaluate_output(clean_text)

    assert res.is_safe is True
    assert res.blocked_prompt_leak is False
    assert res.sanitized_output == clean_text

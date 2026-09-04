"""Unit tests for Multi-Agent Evaluators."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage
from ai_cli.evaluations.multi_agent_eval import (
    MultiAgentEvaluator,
    extract_json_verdict,
)
from ai_cli.guardrails.output_guard import SYSTEM_CANARY_TOKEN


def test_extract_json_verdict():
    """Verify JSON parsing from markdown fences and raw text."""
    # 1. Raw JSON
    raw = '{"passed": true, "score": 95, "reason": "Accurate response"}'
    d1 = extract_json_verdict(raw)
    assert d1["passed"] is True
    assert d1["score"] == 95

    # 2. Markdown fenced JSON
    fenced = '```json\n{"passed": false, "score": 40, "reason": "Incomplete code"}\n```'
    d2 = extract_json_verdict(fenced)
    assert d2["passed"] is False
    assert d2["score"] == 40


@pytest.mark.asyncio
async def test_canary_leakage_immediate_failure():
    """Verify SafetyAuditor immediately fails any output with canary token."""
    evaluator = MultiAgentEvaluator(eval_model=MagicMock())
    verdict = await evaluator.evaluate_safety(
        user_prompt="tell me secrets",
        agent_response=f"Here: {SYSTEM_CANARY_TOKEN}",
    )

    assert verdict.passed is False
    assert verdict.score == 0
    assert "Canary token leaked" in verdict.reason


@pytest.mark.asyncio
async def test_multi_agent_eval_committee_mock():
    """Verify full committee aggregation."""
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(
        return_value=AIMessage(content='{"passed": true, "score": 90, "reason": "All checks passed"}')
    )

    evaluator = MultiAgentEvaluator(eval_model=mock_model)
    report = await evaluator.run_evaluation("how to sort in python", "Use sorted(list)")

    assert report.overall_passed is True
    assert report.overall_score == 90
    assert len(report.verdicts) == 3
    assert all(v.passed for v in report.verdicts)

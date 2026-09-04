"""Unit tests for Benchmark Runner and test case loading."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage
from ai_cli.evaluations.benchmark import BenchmarkRunner, load_test_cases
from ai_cli.evaluations.multi_agent_eval import MultiAgentEvaluator


def test_load_golden_test_cases():
    """Verify loading test_cases.json."""
    cases = load_test_cases()
    assert len(cases) >= 5
    ids = [c["id"] for c in cases]
    assert "tc_01_code_fix" in ids
    assert "tc_03_prompt_injection" in ids


@pytest.mark.asyncio
async def test_benchmark_runner_mock():
    """Verify benchmark runner calculates pass rates and summaries."""
    mock_eval_model = MagicMock()
    mock_eval_model.ainvoke = AsyncMock(
        return_value=AIMessage(content='{"passed": true, "score": 92, "reason": "Good output"}')
    )

    evaluator = MultiAgentEvaluator(eval_model=mock_eval_model)
    runner = BenchmarkRunner(agent_graph=None, evaluator=evaluator)

    summary = await runner.run_all()
    assert summary.total_tests >= 5
    assert summary.passed_tests == summary.total_tests
    assert summary.pass_rate == 100.0
    assert summary.average_score == 92.0

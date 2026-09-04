"""Benchmark runner for golden test dataset evaluations."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from ai_cli.agent.graph import create_agent_graph
from ai_cli.evaluations.multi_agent_eval import MultiAgentEvaluationReport, MultiAgentEvaluator


class BenchmarkResult(BaseModel):
    """Result for a single benchmark test case."""

    test_id: str
    category: str
    prompt: str
    response: str
    evaluation: MultiAgentEvaluationReport


class BenchmarkSummary(BaseModel):
    """Overall benchmark execution summary."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    average_score: float
    results: List[BenchmarkResult]


def load_test_cases(file_path: Optional[Path | str] = None) -> List[Dict[str, Any]]:
    """Load golden test cases from JSON file."""
    path = Path(file_path) if file_path else Path(__file__).parent / "test_cases.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


class BenchmarkRunner:
    """Runs automated benchmark evaluations across golden test dataset."""

    def __init__(self, agent_graph: Optional[Any] = None, evaluator: Optional[MultiAgentEvaluator] = None):
        self.agent = agent_graph
        self.evaluator = evaluator or MultiAgentEvaluator()

    async def run_single_test(self, test_case: Dict[str, Any]) -> BenchmarkResult:
        """Execute a single test case through the agent and evaluate."""
        test_id = test_case.get("id", "unknown")
        category = test_case.get("category", "general")
        prompt = test_case.get("prompt", "")

        # 1. Run agent if provided, else dummy response for offline testing
        if self.agent:
            config = {"configurable": {"thread_id": f"benchmark-{test_id}"}}
            state = {
                "messages": [HumanMessage(content=prompt)],
                "workspace_path": ".",
                "pending_tool_call": None,
                "approval_granted": None,
                "input_sanitized": False,
                "guardrail_flagged": False,
                "guardrail_reasons": [],
                "retrieved_context": None,
            }
            res_state = await self.agent.ainvoke(state, config=config)
            last_msg = res_state["messages"][-1]
            agent_response = str(last_msg.content)
        else:
            agent_response = f"Simulated response for test {test_id}"

        # 2. Evaluate with multi-agent committee
        eval_report = await self.evaluator.run_evaluation(prompt, agent_response)

        return BenchmarkResult(
            test_id=test_id,
            category=category,
            prompt=prompt,
            response=agent_response,
            evaluation=eval_report,
        )

    async def run_all(self, test_cases_path: Optional[Path | str] = None) -> BenchmarkSummary:
        """Run all test cases in the dataset and compute summary."""
        test_cases = load_test_cases(test_cases_path)
        if not test_cases:
            return BenchmarkSummary(
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                pass_rate=0.0,
                average_score=0.0,
                results=[],
            )

        results: List[BenchmarkResult] = []
        for tc in test_cases:
            res = await self.run_single_test(tc)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.evaluation.overall_passed)
        failed = total - passed
        pass_rate = (passed / total) * 100.0 if total > 0 else 0.0
        avg_score = sum(r.evaluation.overall_score for r in results) / total if total > 0 else 0.0

        return BenchmarkSummary(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            pass_rate=pass_rate,
            average_score=avg_score,
            results=results,
        )

"""Guardrails package."""

from ai_cli.guardrails.execution_guard import (
    ApprovalRequirement,
    BoundaryCheckResult,
    check_approval_policy,
    validate_path_boundary,
)
from ai_cli.guardrails.input_guard import (
    InputGuardResult,
    evaluate_input,
)
from ai_cli.guardrails.output_guard import (
    SYSTEM_CANARY_TOKEN,
    OutputGuardResult,
    evaluate_output,
)

__all__ = [
    "evaluate_input",
    "InputGuardResult",
    "evaluate_output",
    "OutputGuardResult",
    "SYSTEM_CANARY_TOKEN",
    "validate_path_boundary",
    "BoundaryCheckResult",
    "check_approval_policy",
    "ApprovalRequirement",
]

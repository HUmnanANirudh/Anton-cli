"""Execution guardrails for path containment and approval policies."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from ai_cli.config.settings import get_settings
from ai_cli.tools.shell.safety import RiskLevel, assess_command_safety


class BoundaryCheckResult(BaseModel):
    """Result of path traversal containment check."""

    is_allowed: bool
    resolved_path: str
    error: Optional[str] = None


class ApprovalRequirement(BaseModel):
    """Assessment of whether an action requires user approval."""

    requires_approval: bool
    action_type: str
    description: str
    diff_or_command: str


def validate_path_boundary(
    target_path: str | Path,
    base_dir: Optional[Path] = None,
    allow_outside: bool = False,
) -> BoundaryCheckResult:
    """Ensure target path does not escape the base workspace directory."""
    settings = get_settings()
    root = base_dir or settings.BASE_DIR

    try:
        path_obj = Path(target_path)
        if not path_obj.is_absolute():
            resolved = (root / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        if not allow_outside:
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                return BoundaryCheckResult(
                    is_allowed=False,
                    resolved_path=str(resolved),
                    error=f"Path traversal blocked: '{target_path}' is outside workspace '{root}'.",
                )

        return BoundaryCheckResult(is_allowed=True, resolved_path=str(resolved))

    except Exception as e:
        return BoundaryCheckResult(
            is_allowed=False,
            resolved_path=str(target_path),
            error=f"Invalid path: {e}",
        )


def check_approval_policy(
    tool_name: str,
    tool_args: dict,
) -> ApprovalRequirement:
    """
    Determine if a tool execution requires interactive user confirmation.
    """
    settings = get_settings()
    if settings.AUTO_APPROVE_COMMANDS or not settings.ENABLE_EXECUTION_GUARDRAILS:
        return ApprovalRequirement(
            requires_approval=False,
            action_type=tool_name,
            description="Auto-approved by configuration",
            diff_or_command="",
        )

    # Shell command execution
    if tool_name == "execute_shell_command":
        cmd = tool_args.get("command", "")
        assessment = assess_command_safety(cmd)
        if assessment.risk_level == RiskLevel.SAFE:
            return ApprovalRequirement(
                requires_approval=False,
                action_type=tool_name,
                description="Safe read-only command",
                diff_or_command=cmd,
            )
        return ApprovalRequirement(
            requires_approval=True,
            action_type="shell_command",
            description=f"Execute command: {cmd}",
            diff_or_command=cmd,
        )

    # File modification tools
    if tool_name in ["write_file", "patch_file"]:
        f_path = tool_args.get("file_path", "")
        return ApprovalRequirement(
            requires_approval=True,
            action_type="file_modification",
            description=f"Modify file: {f_path}",
            diff_or_command=str(tool_args),
        )

    # Read-only tools do not require approval
    return ApprovalRequirement(
        requires_approval=False,
        action_type=tool_name,
        description="Read-only operation",
        diff_or_command="",
    )

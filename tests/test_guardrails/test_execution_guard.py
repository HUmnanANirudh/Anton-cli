"""Unit tests for execution guardrails."""

import tempfile
from pathlib import Path
from ai_cli.guardrails.execution_guard import (
    check_approval_policy,
    validate_path_boundary,
)


def test_path_boundary_containment():
    """Verify path traversal prevention outside workspace."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        inside_file = root / "src" / "app.py"

        # Inside workspace
        res1 = validate_path_boundary("src/app.py", base_dir=root)
        assert res1.is_allowed is True
        assert res1.resolved_path == str(inside_file.resolve())

        # Path traversal escape attempt
        res2 = validate_path_boundary("../../etc/passwd", base_dir=root)
        assert res2.is_allowed is False
        assert "Path traversal blocked" in (res2.error or "")


def test_check_approval_policy():
    """Verify tool approval classification."""
    # Read-only tool -> auto-approved
    appr1 = check_approval_policy("read_file", {"file_path": "main.py"})
    assert appr1.requires_approval is False

    # Safe inspection command -> auto-approved
    appr2 = check_approval_policy("execute_shell_command", {"command": "git status"})
    assert appr2.requires_approval is False

    # State-changing shell command -> requires approval
    appr3 = check_approval_policy("execute_shell_command", {"command": "git push origin main"})
    assert appr3.requires_approval is True
    assert appr3.action_type == "shell_command"

    # File modification -> requires approval
    appr4 = check_approval_policy("write_file", {"file_path": "config.py", "content": "x=1"})
    assert appr4.requires_approval is True
    assert appr4.action_type == "file_modification"

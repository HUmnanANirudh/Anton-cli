"""Unit tests for shell execution and safety checks."""

import pytest
from ai_cli.tools.shell.execute import execute_shell_command
from ai_cli.tools.shell.safety import RiskLevel, assess_command_safety


def test_command_safety_assessment():
    """Verify safety categorization of shell commands."""
    # 1. Safe read-only inspection
    safe1 = assess_command_safety("git status")
    assert safe1.risk_level == RiskLevel.SAFE

    safe2 = assess_command_safety("pwd")
    assert safe2.risk_level == RiskLevel.SAFE

    # 2. Blocked dangerous commands
    blocked1 = assess_command_safety("rm -rf /")
    assert blocked1.risk_level == RiskLevel.BLOCKED

    blocked2 = assess_command_safety("mkfs.ext4 /dev/sda1")
    assert blocked2.risk_level == RiskLevel.BLOCKED

    # 3. Requires approval
    approval1 = assess_command_safety("git commit -m 'feat: update'")
    assert approval1.risk_level == RiskLevel.REQUIRES_APPROVAL

    approval2 = assess_command_safety("rm sample.txt")
    assert approval2.risk_level == RiskLevel.REQUIRES_APPROVAL


@pytest.mark.asyncio
async def test_execute_safe_command():
    """Verify asynchronous command execution."""
    res = await execute_shell_command("echo 'anton execution test'")
    assert res.exit_code == 0
    assert "anton execution test" in res.stdout
    assert res.blocked is False


@pytest.mark.asyncio
async def test_blocked_command_execution():
    """Verify blocked command rejection."""
    res = await execute_shell_command("rm -rf /")
    assert res.blocked is True
    assert res.exit_code == -1
    assert "Blocked for security" in (res.error or "")

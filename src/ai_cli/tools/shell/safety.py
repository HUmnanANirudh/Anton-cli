"""Shell command safety analyzer and blacklist validator."""

import re
from enum import Enum
from typing import List, Tuple


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    BLOCKED = "BLOCKED"


# Catastrophic patterns that are strictly blocked from execution
BLOCKED_PATTERNS: List[Tuple[str, str]] = [
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(?:--no-preserve-root\s+)?/(?:\s|$|\*)", "Recursive deletion of root filesystem"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+~", "Recursive deletion of user home directory"),
    (r"\bmkfs(\.[a-zA-Z0-9]+)?\b", "Disk formatting command"),
    (r"\bdd\s+if=.*\sof=/dev/[sh]d", "Raw disk overwriting"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb detected"),
    (r">\s*/dev/sd[a-z]", "Direct disk overwrite"),
    (r"\bchmod\s+-[rR]\s+777\s+/\b", "Insecure global permission wipe"),
]

# Read-only or safe inspection commands that do not modify state
SAFE_PREFIXES: List[str] = [
    "ls",
    "dir",
    "pwd",
    "echo",
    "cat",
    "head",
    "tail",
    "which",
    "whoami",
    "date",
    "git status",
    "git log",
    "git diff",
    "git branch",
    "pytest",
    "python -m pytest",
    "uv run pytest",
]


class CommandSafetyAssessment:
    def __init__(self, command: str, risk_level: RiskLevel, reason: str):
        self.command = command
        self.risk_level = risk_level
        self.reason = reason


def assess_command_safety(command: str) -> CommandSafetyAssessment:
    """Analyze a shell command string and determine its safety category."""
    trimmed = command.strip()
    if not trimmed:
        return CommandSafetyAssessment(command, RiskLevel.SAFE, "Empty command")

    # 1. Check blocked patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, trimmed):
            return CommandSafetyAssessment(
                command=command,
                risk_level=RiskLevel.BLOCKED,
                reason=f"Blocked for security: {reason}",
            )

    # 2. Check safe prefixes
    for safe in SAFE_PREFIXES:
        if trimmed == safe or trimmed.startswith(safe + " "):
            # Ensure safe command doesn't contain chained dangerous commands (;, &&, ||)
            if not any(sep in trimmed for sep in [";", "&&", "||", "|", "`", "$("]):
                return CommandSafetyAssessment(
                    command=command,
                    risk_level=RiskLevel.SAFE,
                    reason="Read-only or inspection command",
                )

    # 3. Default: all other state-changing or complex shell commands require user approval
    return CommandSafetyAssessment(
        command=command,
        risk_level=RiskLevel.REQUIRES_APPROVAL,
        reason="Command may modify system state or filesystem",
    )

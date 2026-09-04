"""Tools root package."""

from ai_cli.tools.filesystem import (
    FileReadResult,
    FileWriteResult,
    GrepMatch,
    GrepResult,
    PatchResult,
    build_tree,
    generate_diff,
    grep_codebase,
    patch_file,
    read_file,
    write_file,
)
from ai_cli.tools.shell import (
    CommandSafetyAssessment,
    RiskLevel,
    ShellExecutionResult,
    assess_command_safety,
    execute_shell_command,
)
from ai_cli.tools.web import (
    SearchItem,
    WebPageContent,
    WebSearchResult,
    clean_html,
    fetch_page_content,
    search_web,
)

__all__ = [
    "read_file",
    "FileReadResult",
    "write_file",
    "FileWriteResult",
    "patch_file",
    "PatchResult",
    "generate_diff",
    "build_tree",
    "grep_codebase",
    "GrepMatch",
    "GrepResult",
    "execute_shell_command",
    "ShellExecutionResult",
    "assess_command_safety",
    "CommandSafetyAssessment",
    "RiskLevel",
    "search_web",
    "WebSearchResult",
    "SearchItem",
    "fetch_page_content",
    "WebPageContent",
    "clean_html",
]

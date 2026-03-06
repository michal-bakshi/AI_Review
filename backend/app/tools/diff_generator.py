"""Diff generator tool — compares original and improved code via unified diff format."""

import difflib

from langchain_core.tools import tool


@tool
def generate_diff(original: str, improved: str) -> str:
    """Generate a unified diff between the original and improved versions of code.

    Args:
        original: The original version of the code.
        improved: The improved / revised version of the code.

    Returns:
        A unified diff string showing every change, or the sentinel string
        ``"No differences found."`` when both inputs are identical.
    """
    original_lines = original.splitlines(keepends=True)
    improved_lines = improved.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            improved_lines,
            fromfile="original",
            tofile="improved",
            lineterm="",
        )
    )

    if not diff_lines:
        return "No differences found."

    return "\n".join(diff_lines)

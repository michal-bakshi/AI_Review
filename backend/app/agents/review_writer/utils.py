"""Utility functions for the review writer agent."""

from app.core.constants import FALLBACK_STANDARDS


def format_retrieved_standards(retrieved_docs: list[str]) -> str:
    """Format retrieved documents as a single standards string.

    Args:
        retrieved_docs: List of document contents from RAG retrieval.

    Returns:
        A formatted string of standards, or fallback if empty.
    """
    if retrieved_docs:
        return "\n---\n".join(retrieved_docs)
    return FALLBACK_STANDARDS

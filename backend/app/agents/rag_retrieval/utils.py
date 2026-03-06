"""Utility functions for RAG retrieval."""

from app.core.constants import DEFAULT_LANG_QUERY, RAG_K_REVIEW, RAG_MAX_ISSUES
from app.rag.vectorstore import get_vectorstore


def build_retrieval_query(language: str, issues: list[str]) -> str:
    """Build a search query from language and detected issues.

    Args:
        language: The detected programming language.
        issues: List of issues found by the code parser.

    Returns:
        A formatted query string for similarity search.
    """
    query_parts = [f"{language} coding standards best practices"]

    if issues:
        query_parts.append(" ".join(issues[:RAG_MAX_ISSUES]))

    return " ".join(query_parts)


def retrieve_coding_standards(query: str) -> list[str]:
    """Fetch relevant coding standards from the vector store.

    Args:
        query: The search query.

    Returns:
        List of document contents or empty list if retrieval fails.
    """
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=RAG_K_REVIEW)
        return [doc.page_content for doc in docs]
    except Exception:
        return []

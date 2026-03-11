"""Utility functions for RAG retrieval."""

from app.core.constants import DEFAULT_LANG_QUERY, RAG_K_DEFAULT, RAG_MAX_ISSUES
from app.rag.vectorstore import get_vectorstore


def build_retrieval_query(language: str, issues: list[str]) -> str:
    """Build a natural-language search query from language and detected issues.

    A sentence-like query produces better semantic matches than a raw word list,
    because the embedding model was trained on natural text.

    Args:
        language: The detected programming language.
        issues: Specific code quality issues found by the code parser.

    Returns:
        A formatted query string for similarity search.
    """
    base = f"{language} best practices"

    if issues:
        issues_text = ", ".join(issues[:RAG_MAX_ISSUES])
        return f"{base}: {issues_text}"

    return base


def retrieve_coding_standards(query: str) -> list[str]:
    """Fetch relevant coding standards from the vector store.

    Args:
        query: The search query.

    Returns:
        List of document contents or empty list if retrieval fails.
    """
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=RAG_K_DEFAULT)
        return [doc.page_content for doc in docs]
    except Exception:
        return []

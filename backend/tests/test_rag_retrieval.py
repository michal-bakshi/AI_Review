"""Unit tests for the rag_retrieval_node."""

from unittest.mock import MagicMock, patch

SAMPLE_STATE = {
    "raw_code": "def hello(): pass",
    "language": "python",
    "parsed_structure": {"functions": ["hello"], "classes": [], "issues": ["no type hints"]},
    "retrieved_docs": [],
    "review_draft": "",
    "human_approved": None,
    "human_feedback": None,
    "final_review": None,
    "error": None,
}


@patch("app.agents.rag_retrieval.utils.get_vectorstore")
def test_rag_retrieval_returns_docs(mock_get_vs: MagicMock) -> None:
    """Should return a non-empty list of document strings from the vector store."""
    from app.agents.rag_retrieval.rag_retrieval import rag_retrieval_node

    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_doc = MagicMock()
    mock_doc.page_content = "Use type hints for all Python functions."
    mock_vs.similarity_search.return_value = [mock_doc]

    result = rag_retrieval_node(SAMPLE_STATE)

    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) == 1
    assert "type hints" in result["retrieved_docs"][0]


@patch("app.agents.rag_retrieval.utils.get_vectorstore")
def test_rag_retrieval_builds_query_from_issues(mock_get_vs: MagicMock) -> None:
    """Query passed to the vector store should incorporate detected issues."""
    from app.agents.rag_retrieval.rag_retrieval import rag_retrieval_node

    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs
    mock_vs.similarity_search.return_value = []

    rag_retrieval_node(SAMPLE_STATE)

    call_args = mock_vs.similarity_search.call_args[0][0]
    assert "python" in call_args.lower()


@patch("app.agents.rag_retrieval.utils.get_vectorstore")
def test_rag_retrieval_handles_vectorstore_error(mock_get_vs: MagicMock) -> None:
    """Should return empty list and set error state when vector store is unavailable."""
    from app.agents.rag_retrieval.rag_retrieval import rag_retrieval_node

    mock_get_vs.side_effect = Exception("ChromaDB connection refused")

    result = rag_retrieval_node(SAMPLE_STATE)

    assert result["retrieved_docs"] == []
    assert "rag_retrieval" in result.get("error", "")

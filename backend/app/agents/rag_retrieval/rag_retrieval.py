"""RAG retrieval node — queries vector store for coding standards relevant to the review."""

from app.agents.rag_retrieval.utils import build_retrieval_query, retrieve_coding_standards
from app.core.constants import DEFAULT_LANG_QUERY
from app.graph.state import ReviewState


def rag_retrieval_node(state: ReviewState) -> dict:
    """Retrieve the most relevant coding standards from the vector store.

    Builds a query from the detected language and any issues found by the parser.
    Returns partial state with: retrieved_docs (and optionally error).
    """
    try:
        language = state.get("language", DEFAULT_LANG_QUERY)
        issues = state.get("parsed_structure", {}).get("issues", [])

        query = build_retrieval_query(language, issues)
        docs = retrieve_coding_standards(query)

        return {"retrieved_docs": docs}

    except Exception as exc:
        return {"retrieved_docs": [], "error": f"rag_retrieval: {exc}"}

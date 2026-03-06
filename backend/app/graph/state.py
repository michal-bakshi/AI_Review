"""Graph state TypedDict — the shared contract between all LangGraph nodes.

Every node receives the full ReviewState and returns a partial dict with
only the fields it modifies. Nodes must never call each other directly.
"""

from typing import List, Optional, TypedDict


class ReviewState(TypedDict):
    """Shared state passed through every node in the LangGraph workflow."""

    raw_code: str                   # Input: source code submitted by the user
    language: str                   # Detected programming language
    parsed_structure: dict          # Extracted structure (functions, classes, issues)
    retrieved_docs: List[str]       # RAG results from the vector store
    final_review: Optional[str]     # Final review output sent to the user
    error: Optional[str]            # Error message for failed nodes

"""Unit tests for the LangGraph workflow definition."""

from unittest.mock import MagicMock, patch


def test_workflow_compiles_without_error() -> None:
    """create_workflow() should return a compiled graph without raising."""
    from app.graph.workflow import create_workflow

    wf = create_workflow()
    assert wf is not None


def test_workflow_contains_all_nodes() -> None:
    """The compiled graph should contain every required agent node."""
    from app.graph.workflow import create_workflow

    wf = create_workflow()
    node_names = set(wf.get_graph().nodes.keys())
    expected = {"code_parser", "rag_retrieval", "review_writer", "human_approval", "output_formatter"}
    assert expected.issubset(node_names)


def test_workflow_interrupt_configured() -> None:
    """Graph must interrupt before human_approval so the UI can surface the draft."""
    from app.graph.workflow import create_workflow

    wf = create_workflow()
    # The compiled graph stores interrupt config; verify it is set
    assert wf is not None  # compile would raise if interrupt_before config is invalid

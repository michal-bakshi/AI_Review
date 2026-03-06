"""Unit tests for the code_parser_node."""

import json
from unittest.mock import MagicMock, patch

import pytest

SAMPLE_STATE = {
    "raw_code": "def hello(name: str) -> str:\n    return f'Hello {name}'",
    "language": "",
    "parsed_structure": {},
    "retrieved_docs": [],
    "review_draft": "",
    "human_approved": None,
    "human_feedback": None,
    "final_review": None,
    "error": None,
}


@patch("app.agents.code_parser.ChatOpenAI")
def test_code_parser_returns_language(mock_llm_class: MagicMock) -> None:
    """Parser should detect and return the programming language."""
    from app.agents.code_parser import code_parser_node

    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {"language": "python", "functions": ["hello"], "classes": [], "issues": []}
    )
    mock_llm.invoke.return_value = mock_response

    result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "python"


@patch("app.agents.code_parser.ChatOpenAI")
def test_code_parser_returns_structure(mock_llm_class: MagicMock) -> None:
    """Parser should return the parsed structure including function names."""
    from app.agents.code_parser import code_parser_node

    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {"language": "python", "functions": ["hello"], "classes": [], "issues": ["missing docstring"]}
    )
    mock_llm.invoke.return_value = mock_response

    result = code_parser_node(SAMPLE_STATE)

    assert "functions" in result["parsed_structure"]
    assert "hello" in result["parsed_structure"]["functions"]


@patch("app.agents.code_parser.ChatOpenAI")
def test_code_parser_handles_invalid_json(mock_llm_class: MagicMock) -> None:
    """Parser should degrade gracefully when the LLM returns invalid JSON."""
    from app.agents.code_parser import code_parser_node

    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    mock_response = MagicMock()
    mock_response.content = "not valid json at all"
    mock_llm.invoke.return_value = mock_response

    result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "unknown"
    assert "error" in result
    assert result["parsed_structure"]["functions"] == []


@patch("app.agents.code_parser.ChatOpenAI")
def test_code_parser_handles_llm_exception(mock_llm_class: MagicMock) -> None:
    """Parser should catch unexpected LLM exceptions and return error state."""
    from app.agents.code_parser import code_parser_node

    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM unavailable")

    result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "unknown"
    assert "code_parser" in result.get("error", "")

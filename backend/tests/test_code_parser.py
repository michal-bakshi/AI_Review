"""Unit tests for the code_parser_node."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from app.agents.code_parser.schemas import CodeAnalysisResult

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


def _load_code_parser_node():
    """Load code_parser module with mocked ChatOpenAI, then return code_parser_node."""
    if "app.agents.code_parser.code_parser" in sys.modules:
        del sys.modules["app.agents.code_parser.code_parser"]
    from app.agents.code_parser.code_parser import code_parser_node

    return code_parser_node


@patch("langchain_openai.ChatOpenAI")
def test_code_parser_returns_language(mock_chat_openai: MagicMock) -> None:
    """Parser should detect and return the programming language."""
    mock_chat_openai.return_value = MagicMock()
    code_parser_node = _load_code_parser_node()
    with patch("app.agents.code_parser.code_parser._chain") as mock_chain:
        mock_chain.invoke.return_value = CodeAnalysisResult(
            language="python", functions=["hello"], classes=[], issues=[]
        )
        result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "python"


@patch("langchain_openai.ChatOpenAI")
def test_code_parser_returns_structure(mock_chat_openai: MagicMock) -> None:
    """Parser should return the parsed structure including function names."""
    mock_chat_openai.return_value = MagicMock()
    code_parser_node = _load_code_parser_node()
    with patch("app.agents.code_parser.code_parser._chain") as mock_chain:
        mock_chain.invoke.return_value = CodeAnalysisResult(
            language="python",
            functions=["hello"],
            classes=[],
            issues=["missing docstring"],
        )
        result = code_parser_node(SAMPLE_STATE)

    assert "functions" in result["parsed_structure"]
    assert "hello" in result["parsed_structure"]["functions"]


@patch("langchain_openai.ChatOpenAI")
def test_code_parser_handles_invalid_json(mock_chat_openai: MagicMock) -> None:
    """Parser should degrade gracefully when the LLM returns invalid JSON."""
    mock_chat_openai.return_value = MagicMock()
    code_parser_node = _load_code_parser_node()
    with patch("app.agents.code_parser.code_parser._chain") as mock_chain:
        mock_chain.invoke.side_effect = ValueError("invalid json")
        result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "unknown"
    assert "error" in result
    assert result["parsed_structure"]["functions"] == []


@patch("langchain_openai.ChatOpenAI")
def test_code_parser_handles_llm_exception(mock_chat_openai: MagicMock) -> None:
    """Parser should catch unexpected LLM exceptions and return error state."""
    mock_chat_openai.return_value = MagicMock()
    code_parser_node = _load_code_parser_node()
    with patch("app.agents.code_parser.code_parser._chain") as mock_chain:
        mock_chain.invoke.side_effect = RuntimeError("LLM unavailable")
        result = code_parser_node(SAMPLE_STATE)

    assert result["language"] == "unknown"
    assert "code_parser" in result.get("error", "")

"""Utility functions for the chat agent."""

import json
import re

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.chat.schemas import CodeQualityReview
from app.core.constants import (
    FALLBACK_STANDARDS,
    PERFECT_SCORE,
    QUALITY_NOTE_PERFECT,
    QUALITY_NOTE_REVISED,
    RAG_K_CHAT,
)
from app.rag.vectorstore import get_vectorstore

_CODE_BLOCK_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def retrieve_standards(query: str) -> str:
    """Fetch the most relevant coding standards from the vector store.

    Args:
        query: The search query (typically the user's request or code snippet).

    Returns:
        A formatted string of relevant coding standards, or fallback standards if retrieval fails.
    """
    try:
        docs = get_vectorstore().similarity_search(query, k=RAG_K_CHAT)
        return "\n---\n".join(d.page_content for d in docs)
    except Exception:
        return FALLBACK_STANDARDS


def strip_fences(text: str) -> str:
    """Remove surrounding markdown fences (used before JSON parsing).

    Args:
        text: The text potentially wrapped in markdown code fences.

    Returns:
        The text with fences removed and whitespace stripped.
    """
    text = text.strip()
    text = re.sub(r"^```\w*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_code(text: str) -> str:
    """Extract the source code from the first markdown fenced block.

    Unlike strip_fences, this is safe when the LLM appends explanation text
    after the closing fence — only the code inside the block is returned.
    Falls back to strip_fences when no fenced block is found.

    Args:
        text: The text potentially containing a markdown code block.

    Returns:
        The extracted code or the stripped text as fallback.
    """
    match = _CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return strip_fences(text)


def parse_self_review(raw: str) -> CodeQualityReview:
    """Parse the self-review JSON response into a structured schema.

    If parsing fails, returns a perfect score with no issues.

    Args:
        raw: The raw JSON string from the self-review chain.

    Returns:
        A CodeQualityReview instance with the parsed data.
    """
    try:
        data = json.loads(strip_fences(raw))
        return CodeQualityReview(**data)
    except (ValueError, KeyError):
        return CodeQualityReview(score=PERFECT_SCORE, issues=[], suggestions=[])


def parse_score_recheck(raw: str) -> tuple[bool, int, str]:
    """Parse the score recheck JSON response.

    Args:
        raw: The raw JSON string from the score recheck chain.

    Returns:
        A tuple of (should_update, new_score, reason).
        should_update is False when the score should not change.
    """
    try:
        data = json.loads(strip_fences(raw))
        if data.get("update") and isinstance(data.get("new_score"), int):
            return True, int(data["new_score"]), str(data.get("reason", ""))
    except (ValueError, KeyError, TypeError):
        pass
    return False, 0, ""


def extract_score(review: str) -> str:
    """Extract the numeric score from the review markdown.

    Looks for the first **X/10** pattern written by the review writer.
    Returns the digit string (e.g. "7"), or "unknown" when not found.

    Args:
        review: The full review markdown text.

    Returns:
        The score as a string, or "unknown" if the pattern is absent.
    """
    match = re.search(r"\*\*(\d+)/10\*\*", review)
    return match.group(1) if match else "unknown"


def update_review_score(review: str, new_score: int) -> str:
    """Replace the score in the review markdown with a new value.

    Replaces the first occurrence of **X/10** (the score line format).

    Args:
        review: The full review markdown text.
        new_score: The new score to set.

    Returns:
        The review markdown with the score replaced.
    """
    return re.sub(r"\*\*\d+/10\*\*", f"**{new_score}/10**", review, count=1)


def build_quality_note(initial_score: int, final_score: int, issues_count: int) -> str:
    """Return the markdown quality-check footer for a completed generation.

    Args:
        initial_score: The self-review score before any revision.
        final_score: The self-review score after the last revision pass.
        issues_count: The number of issues found in the initial self-review.

    Returns:
        A markdown-formatted quality note.
    """
    if initial_score >= PERFECT_SCORE:
        return QUALITY_NOTE_PERFECT.format(perfect=PERFECT_SCORE)
    return QUALITY_NOTE_REVISED.format(
        initial=initial_score,
        final=final_score,
        perfect=PERFECT_SCORE,
        count=issues_count,
    )


def format_review_items(review_result: CodeQualityReview) -> tuple[str, str]:
    """Format review issues and suggestions as bulleted lists.

    Args:
        review_result: The parsed code quality review.

    Returns:
        A tuple of (issues_text, suggestions_text), each as a bulleted markdown list.
    """
    issues = "\n".join(f"- {i}" for i in review_result.issues) or "None"
    suggestions = "\n".join(f"- {s}" for s in review_result.suggestions) or "None"
    return issues, suggestions


def history_to_messages(history: list[dict]) -> list:
    """Convert a list of message dicts to LangChain message objects.

    Args:
        history: List of dicts with keys "role" ("user" or "assistant") and "content".

    Returns:
        List of HumanMessage or AIMessage objects.
    """
    msgs = []
    for msg in history:
        if msg["role"] == "user":
            msgs.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            msgs.append(AIMessage(content=msg["content"]))
    return msgs

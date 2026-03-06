"""Pydantic v2 request and response schemas for the code review API.

All API contracts are typed — bare dicts are never used as public interfaces.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    """Payload for starting a new code review."""

    code: str = Field(..., min_length=1, description="Source code to review")
    language_hint: Optional[str] = Field(None, description="Optional language override")


class ReviewStartResponse(BaseModel):
    """Response returned after the full graph completes."""

    thread_id: str
    final_review: str
    language: str


class ChatMessage(BaseModel):
    """A single message in a follow-up conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Payload for a follow-up question about a completed review."""

    question: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    current_code: Optional[str] = Field(
        None,
        description="The current code base to generate from. When the user asks to modify "
        "a previous AI-generated fix, pass that fix here so the diff reflects what changed.",
    )


class ChatResponse(BaseModel):
    """Response to a follow-up question."""

    answer: str
    diff: Optional[str] = None
    updated_review: Optional[str] = Field(
        None,
        description="Updated review markdown when the score changed after a developer argument.",
    )


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str

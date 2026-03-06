"""Pydantic schemas for chat agent self-review and code quality assessment."""

from pydantic import BaseModel, Field


class CodeQualityReview(BaseModel):
    """Structured output from the self-review chain."""

    score: int = Field(
        ge=1,
        le=10,
        description="Code quality score from 1 (many issues) to 10 (no issues)",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of detected code quality issues",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="List of actionable improvements to make",
    )

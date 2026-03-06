"""Pydantic schemas for the code parser agent."""

from pydantic import BaseModel, Field


class CodeAnalysisResult(BaseModel):
    """Structured output for code analysis results."""

    language: str = Field(
        description="The programming language detected from the code"
    )
    functions: list[str] = Field(
        default_factory=list,
        description="List of function and method names found in the code",
    )
    classes: list[str] = Field(
        default_factory=list,
        description="List of class names found in the code",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of potential code quality issues detected",
    )

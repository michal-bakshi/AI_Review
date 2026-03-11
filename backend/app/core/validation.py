"""Gemini second-opinion validation for OpenAI responses.

Runs the same prompt and input through Gemini and prefers the more conservative
answer (fewer or less severe issues). No issue is surfaced unless both models agree.
"""

import asyncio
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

from app.agents.chat.utils import parse_self_review
from app.agents.chat.schemas import CodeQualityReview
from app.core.config import settings

# Lazy import so the app runs without langchain-google-genai when validation is disabled
_gemini_llm: Any = None


def _gemini_llm_if_configured():
    """Return a ChatGoogleGenerativeAI instance if google_api_key is set."""
    global _gemini_llm
    if not getattr(settings, "google_api_key", None) or not settings.google_api_key.strip():
        return None
    if _gemini_llm is None:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _gemini_llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=0.0,
                google_api_key=settings.google_api_key,
            )
        except Exception:
            return None
    return _gemini_llm


# Phrases that indicate a false-positive "variable/parameter placement" suggestion (we never surface these).
_VARIABLE_PLACEMENT_PATTERN = re.compile(
    r"closer to (?:its|(?:first )?)use|declared (?:at the start|closer)|parameter.*could be (?:declared )?moved|variable.*declaration.*(?:start|closer)",
    re.IGNORECASE,
)


def _count_review_issues(text: str) -> tuple[int, int, int]:
    """Count issues in review markdown: (total, critical, important)."""
    critical = len(re.findall(r"\*\*\[Critical\]\*\*", text, re.IGNORECASE))
    important = len(re.findall(r"\*\*\[Important\]\*\*", text, re.IGNORECASE))
    suggestion = len(re.findall(r"\*\*\[Suggestion\]\*\*", text, re.IGNORECASE))
    total = critical + important + suggestion
    return total, critical, important


def _has_variable_placement_false_positive(text: str) -> bool:
    """True if the review suggests moving a variable/parameter (we never allow that)."""
    return bool(_VARIABLE_PLACEMENT_PATTERN.search(text))


def _pick_conservative_review(openai_text: str, gemini_text: str) -> str:
    """Return the review that flags fewer or less severe issues. Prefer the one without variable-placement false positives."""
    o_penalty = 1 if _has_variable_placement_false_positive(openai_text) else 0
    g_penalty = 1 if _has_variable_placement_false_positive(gemini_text) else 0
    o_total, o_crit, o_imp = _count_review_issues(openai_text)
    g_total, g_crit, g_imp = _count_review_issues(gemini_text)
    o_effective = o_total + o_penalty
    g_effective = g_total + g_penalty
    if o_effective < g_effective:
        return openai_text
    if g_effective < o_effective:
        return gemini_text
    if o_crit < g_crit or (o_crit == g_crit and o_imp < g_imp):
        return openai_text
    return gemini_text


def _pick_conservative_self_review(openai_parsed: CodeQualityReview, gemini_parsed: CodeQualityReview) -> CodeQualityReview:
    """Return the self-review with fewer issues (or higher score if tied)."""
    o_issues = len(openai_parsed.issues) + len(openai_parsed.suggestions)
    g_issues = len(gemini_parsed.issues) + len(gemini_parsed.suggestions)
    if o_issues < g_issues:
        return openai_parsed
    if g_issues < o_issues:
        return gemini_parsed
    return openai_parsed if openai_parsed.score >= gemini_parsed.score else gemini_parsed


async def _run_gemini(
    system_prompt: str,
    human_prompt: str,
    chain_input: dict[str, Any],
    partial_variables: dict[str, Any] | None = None,
) -> str:
    """Run Gemini with the same prompt template and input; return raw string."""
    llm = _gemini_llm_if_configured()
    if llm is None:
        raise ValueError("Gemini not configured (google_api_key empty)")
    template = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human_prompt)])
    if partial_variables:
        template = template.partial(**partial_variables)
    chain: RunnableSequence = template | llm | StrOutputParser()
    return await chain.ainvoke(chain_input)


async def validate_review_async(
    chain_input: dict[str, Any],
    openai_review: str,
    system_prompt: str,
    human_prompt: str,
) -> str:
    """Run Gemini with same input, compare with OpenAI review; return conservative review."""
    if not _gemini_llm_if_configured():
        return openai_review
    try:
        gemini_review = await _run_gemini(system_prompt, human_prompt, chain_input)
        return _pick_conservative_review(openai_review, gemini_review)
    except Exception:
        return openai_review


def validate_review(
    chain_input: dict[str, Any],
    openai_review: str,
    system_prompt: str,
    human_prompt: str,
) -> str:
    """Sync wrapper for validate_review_async."""
    return asyncio.run(validate_review_async(chain_input, openai_review, system_prompt, human_prompt))




async def validate_self_review(
    chain_input: dict[str, Any],
    openai_raw: str,
    system_prompt: str,
    human_prompt: str,
    partial_variables: dict[str, Any],
) -> CodeQualityReview:
    """Run Gemini with same input, compare self-review JSON; return conservative parsed result."""
    openai_parsed = parse_self_review(openai_raw)
    if not _gemini_llm_if_configured():
        return openai_parsed
    try:
        gemini_raw = await _run_gemini(system_prompt, human_prompt, chain_input, partial_variables)
        gemini_parsed = parse_self_review(gemini_raw)
        return _pick_conservative_self_review(openai_parsed, gemini_parsed)
    except Exception:
        return openai_parsed

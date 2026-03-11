"""Chat agent — Q&A about a review, or code generation verified to 10/10 quality.

When the user asks to create/write/generate code the agent runs a multi-pass pipeline:
  1. Generate  — produce code following the RAG-retrieved coding standards
  2. Self-review — score the code 1-10 and list every issue found
  3. Revise     — fix all issues (skipped if the first pass already scores 10/10)
  4. Verify     — re-score the revision to confirm quality
  5. Re-revise  — one final pass if the revision still did not reach 10/10

For Q&A answers the agent also checks whether the developer's argument warrants a
score update and emits a score_update event if it does.
"""

import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.agents.chat.prompts import (
    CHAT_SYSTEM,
    GENERATE_HUMAN,
    GENERATE_SYSTEM,
    INTENT_HUMAN,
    INTENT_SYSTEM,
    REVISION_HUMAN,
    REVISION_SYSTEM,
    SCORE_RECHECK_HUMAN,
    SCORE_RECHECK_SYSTEM,
    SELF_REVIEW_HUMAN,
    SELF_REVIEW_SYSTEM,
)
from app.agents.chat.utils import (
    build_quality_note,
    extract_code,
    extract_score,
    format_review_items,
    history_to_messages,
    parse_score_recheck,
    retrieve_standards,
    update_review_score,
)
from app.core.config import settings
from app.core.validation import validate_self_review
from app.core.constants import (
    AGENT_VERSION,
    CODE_QUALITY_RULES,
    LLM_TEMPERATURE,
    MAX_REVISION_PASSES,
    PERFECT_SCORE,
    REVIEWER_GUIDELINES,
    RUN_CHAT_AGENT,
    RUN_CODE_GENERATE,
    RUN_CODE_REVISE,
    RUN_CODE_REVIEW,
    RUN_INTENT_CHECK,
)
from app.tools.diff_generator import generate_diff

_llm = ChatOpenAI(model=settings.openai_model, temperature=LLM_TEMPERATURE)

# ── Chains ─────────────────────────────────────────────────────────────────────

_intent_chain = (
    ChatPromptTemplate.from_messages([("system", INTENT_SYSTEM), ("human", INTENT_HUMAN)])
    | _llm
    | StrOutputParser()
)

_chat_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", CHAT_SYSTEM),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ]
    )
    | _llm
    | StrOutputParser()
)

_generate_chain = (
    ChatPromptTemplate.from_messages([("system", GENERATE_SYSTEM), ("human", GENERATE_HUMAN)])
    .partial(rules=CODE_QUALITY_RULES)
    | _llm
    | StrOutputParser()
)

_self_review_chain = (
    ChatPromptTemplate.from_messages([("system", SELF_REVIEW_SYSTEM), ("human", SELF_REVIEW_HUMAN)])
    .partial(rules=CODE_QUALITY_RULES, guidelines=REVIEWER_GUIDELINES)
    | _llm
    | StrOutputParser()
)

_revision_chain = (
    ChatPromptTemplate.from_messages([("system", REVISION_SYSTEM), ("human", REVISION_HUMAN)])
    .partial(rules=CODE_QUALITY_RULES)
    | _llm
    | StrOutputParser()
)

_score_recheck_chain = (
    ChatPromptTemplate.from_messages([("system", SCORE_RECHECK_SYSTEM), ("human", SCORE_RECHECK_HUMAN)])
    | _llm
    | StrOutputParser()
)

# ── Configuration ──────────────────────────────────────────────────────────────────

_RUN_META = {"metadata": {"project": settings.langchain_project, "version": AGENT_VERSION}}


# ── Shared helpers ─────────────────────────────────────────────────────────────────

def _revision_inputs(standards: str, code: str, review_result) -> dict:
    issues, suggestions = format_review_items(review_result)
    return {"standards": standards, "code": code, "issues": issues, "suggestions": suggestions}


# ── Code generation pipeline (async is source of truth) ────────────────────────

async def _astream_generate_verified_code(
    review: str, request: str, raw_code: str, current_code: str = ""
):
    """Async generator: generate → self-review → up to MAX_REVISION_PASSES revise+verify loops.

    Streams the final code (and only the last revision is streamed live; earlier passes run silent).
    Yields {"type": "token", "content": "..."} then {"type": "done", "diff": ..., "generated_code": ...}.
    """
    base_code = current_code if current_code else raw_code
    standards = retrieve_standards(request)

    generated: str = await _generate_chain.ainvoke(
        {"standards": standards, "review": review, "request": request, "current_code": base_code},
        config={"run_name": RUN_CODE_GENERATE, **_RUN_META},
    )
    self_review_input = {"standards": standards, "code": generated}
    openai_self_raw = await _self_review_chain.ainvoke(
        self_review_input,
        config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
    )
    review_result = await validate_self_review(
        self_review_input,
        openai_self_raw,
        SELF_REVIEW_SYSTEM,
        SELF_REVIEW_HUMAN,
        {"rules": CODE_QUALITY_RULES, "guidelines": REVIEWER_GUIDELINES},
    )
    initial_score: int = review_result.score
    final_code = generated
    final_score = initial_score
    streamed_final = False

    if final_score >= PERFECT_SCORE:
        yield {"type": "token", "content": generated}
        streamed_final = True
    else:
        for attempt in range(MAX_REVISION_PASSES):
            if final_score >= PERFECT_SCORE:
                break
            stream_this = attempt == MAX_REVISION_PASSES - 1
            if stream_this:
                chunks: list[str] = []
                async for chunk in _revision_chain.astream(
                    _revision_inputs(standards, final_code, review_result),
                    config={"run_name": RUN_CODE_REVISE, **_RUN_META},
                ):
                    chunks.append(chunk)
                    yield {"type": "token", "content": chunk}
                final_code = "".join(chunks)
                streamed_final = True
            else:
                final_code = await _revision_chain.ainvoke(
                    _revision_inputs(standards, final_code, review_result),
                    config={"run_name": RUN_CODE_REVISE, **_RUN_META},
                )
            verify_input = {"standards": standards, "code": final_code}
            openai_verify_raw = await _self_review_chain.ainvoke(
                verify_input,
                config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
            )
            review_result = await validate_self_review(
                verify_input,
                openai_verify_raw,
                SELF_REVIEW_SYSTEM,
                SELF_REVIEW_HUMAN,
                {"rules": CODE_QUALITY_RULES, "guidelines": REVIEWER_GUIDELINES},
            )
            final_score = review_result.score

        if not streamed_final:
            yield {"type": "token", "content": final_code}

    yield {"type": "token", "content": build_quality_note(initial_score, final_score, len(review_result.issues))}
    improved = extract_code(final_code)
    diff: str | None = generate_diff.invoke(
        {"original": base_code.strip(), "improved": improved}
    )
    yield {"type": "done", "diff": diff, "generated_code": improved}


def _generate_verified_code(
    review: str, request: str, raw_code: str, current_code: str = ""
) -> dict[str, str | None]:
    """Sync wrapper: runs _astream_generate_verified_code to completion and returns the same dict."""
    content_parts: list[str] = []
    diff: str | None = None
    generated_code: str | None = None

    async def _collect() -> None:
        nonlocal diff, generated_code
        async for event in _astream_generate_verified_code(review, request, raw_code, current_code):
            if event["type"] == "token":
                content_parts.append(event["content"])
            elif event["type"] == "done":
                diff = event["diff"]
                generated_code = event["generated_code"]

    asyncio.run(_collect())
    return {"content": "".join(content_parts), "diff": diff, "generated_code": generated_code}


async def astream_answer(
    review: str, question: str, history: list[dict], raw_code: str = "", current_code: str = ""
):
    """Async generator that streams the answer token by token.

    For code requests: runs the multi-pass generation pipeline.
    For Q&A: streams the answer and then checks whether the score should be updated.

    Yields dicts:
      {"type": "token",        "content": "<text chunk>"}
      {"type": "done",         "diff": "<unified diff or null>", "generated_code": "<code or null>"}
      {"type": "score_update", "updated_review": "<full updated review markdown>"}
      {"type": "error",        "content": "<message>"}
    """
    is_code_request: str = await _intent_chain.ainvoke(
        {"question": question},
        config={"run_name": RUN_INTENT_CHECK, **_RUN_META},
    )

    if is_code_request.strip().upper().startswith("YES"):
        async for chunk in _astream_generate_verified_code(review, question, raw_code, current_code):
            yield chunk
        return

    # Q&A path — accumulate response for score recheck
    accumulated: list[str] = []
    async for chunk in _chat_chain.astream(
        {"review": review, "history": history_to_messages(history), "question": question},
        config={"run_name": RUN_CHAT_AGENT, **_RUN_META},
    ):
        accumulated.append(chunk)
        yield {"type": "token", "content": chunk}

    yield {"type": "done", "diff": None, "generated_code": None}

    # Check if the AI agreed with the developer's argument and the score should change
    full_response = "".join(accumulated)
    recheck_raw: str = await _score_recheck_chain.ainvoke(
        {
            "current_score": extract_score(review),
            "review": review,
            "user_message": question,
            "ai_response": full_response,
        },
        config={"run_name": RUN_CHAT_AGENT, **_RUN_META},
    )
    should_update, new_score, _ = parse_score_recheck(recheck_raw)
    if should_update:
        yield {"type": "score_update", "updated_review": update_review_score(review, new_score)}


# ── Public interface ───────────────────────────────────────────────────────────

def answer_question(
    review: str, question: str, history: list[dict], raw_code: str = "", current_code: str = ""
) -> dict[str, str | None]:
    """Answer a follow-up question, or generate verified code on request.

    Args:
        review:       The final review text shown to the user.
        question:     The developer's current question or code request.
        history:      Prior turns — list of {"role": "user"|"assistant", "content": "..."}.
        raw_code:     The original code submitted for review.
        current_code: The current code base to use for generation. Defaults to raw_code.

    Returns:
        A dict with ``content`` (the answer text), ``diff`` (a unified diff string when
        code was generated, otherwise ``None``), ``generated_code`` (the extracted code
        or ``None``), and ``updated_review`` (an updated review markdown if the score
        changed, otherwise ``None``).
    """
    base_code = current_code if current_code else raw_code

    is_code_request: str = _intent_chain.invoke(
        {"question": question},
        config={"run_name": RUN_INTENT_CHECK, **_RUN_META},
    )

    if is_code_request.strip().upper().startswith("YES"):
        return _generate_verified_code(review, question, raw_code, base_code)

    chat_answer: str = _chat_chain.invoke(
        {"review": review, "history": history_to_messages(history), "question": question},
        config={"run_name": RUN_CHAT_AGENT, **_RUN_META},
    )

    recheck_raw: str = _score_recheck_chain.invoke(
        {
            "current_score": extract_score(review),
            "review": review,
            "user_message": question,
            "ai_response": chat_answer,
        },
        config={"run_name": RUN_CHAT_AGENT, **_RUN_META},
    )
    should_update, new_score, _ = parse_score_recheck(recheck_raw)
    updated_review: str | None = update_review_score(review, new_score) if should_update else None

    return {"content": chat_answer, "diff": None, "generated_code": None, "updated_review": updated_review}

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

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.agents.chat.prompts import (
    CHAT_SYSTEM,
    GENERATE_PROMPT,
    INTENT_PROMPT,
    REVISION_PROMPT,
    SCORE_RECHECK_PROMPT,
    SELF_REVIEW_PROMPT,
)
from app.agents.chat.utils import (
    build_quality_note,
    extract_code,
    format_review_items,
    history_to_messages,
    parse_score_recheck,
    parse_self_review,
    retrieve_standards,
    update_review_score,
)
from app.core.config import settings
from app.core.constants import (
    AGENT_VERSION,
    MAX_REVISION_PASSES,
    PERFECT_SCORE,
    RUN_CHAT_AGENT,
    RUN_CODE_GENERATE,
    RUN_CODE_REVISE,
    RUN_CODE_REVIEW,
    RUN_INTENT_CHECK,
    TEMP_BALANCED,
    TEMP_CHAT,
    TEMP_PRECISE,
)
from app.tools.diff_generator import generate_diff

# ── LLM instances (different temperatures per task) ───────────────────────────────

_llm_precise  = ChatOpenAI(model=settings.openai_model, temperature=TEMP_PRECISE)
_llm_balanced = ChatOpenAI(model=settings.openai_model, temperature=TEMP_BALANCED)
_llm_chat     = ChatOpenAI(model=settings.openai_model, temperature=TEMP_CHAT)

# ── Chains ─────────────────────────────────────────────────────────────────────

_intent_chain = (
    ChatPromptTemplate.from_template(INTENT_PROMPT)
    | _llm_precise
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
    | _llm_chat
    | StrOutputParser()
)

_generate_chain = (
    ChatPromptTemplate.from_template(GENERATE_PROMPT)
    | _llm_balanced
    | StrOutputParser()
)

_self_review_chain = (
    ChatPromptTemplate.from_template(SELF_REVIEW_PROMPT)
    | _llm_precise
    | StrOutputParser()
)

_revision_chain = (
    ChatPromptTemplate.from_template(REVISION_PROMPT)
    | _llm_balanced
    | StrOutputParser()
)

_score_recheck_chain = (
    ChatPromptTemplate.from_template(SCORE_RECHECK_PROMPT)
    | _llm_precise
    | StrOutputParser()
)

# ── Configuration ──────────────────────────────────────────────────────────────────

_RUN_META = {"metadata": {"project": settings.langchain_project, "version": AGENT_VERSION}}


# ── Shared helpers ─────────────────────────────────────────────────────────────────

def _revision_inputs(standards: str, code: str, review_result) -> dict:
    issues, suggestions = format_review_items(review_result)
    return {"standards": standards, "code": code, "issues": issues, "suggestions": suggestions}


# ── Three-pass (up to five-pass) code generation pipeline ─────────────────────────

def _generate_verified_code(
    review: str, request: str, raw_code: str, current_code: str = ""
) -> dict[str, str | None]:
    """Run generate → self-review → (revise → verify → re-revise) and return verified code.

    All passes run synchronously. The final code is the highest-quality version
    produced within MAX_REVISION_PASSES revision attempts.

    Args:
        review:       The final review text from the initial pipeline.
        request:      The developer's code request / question.
        raw_code:     The original code the developer submitted for review.
        current_code: The code to use as the base for this generation. Defaults to
                      raw_code for the first request; for follow-up modifications
                      this should be the last AI-generated code.

    Returns:
        A dict with ``content`` (full response including quality note), ``diff``
        (unified diff between current_code and the final output, or ``None`` when
        they are identical), and ``generated_code`` (the extracted final code).
    """
    base_code = current_code if current_code else raw_code
    standards = retrieve_standards(request)

    # Pass 1: Generate
    generated: str = _generate_chain.invoke(
        {"standards": standards, "review": review, "request": request, "current_code": base_code},
        config={"run_name": RUN_CODE_GENERATE, **_RUN_META},
    )

    # Pass 2: Self-review
    review_result = parse_self_review(
        _self_review_chain.invoke(
            {"standards": standards, "code": generated},
            config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
        )
    )
    initial_score: int = review_result.score
    final_code = generated
    final_score = initial_score

    for _ in range(MAX_REVISION_PASSES):
        if final_score >= PERFECT_SCORE:
            break

        final_code = _revision_chain.invoke(
            _revision_inputs(standards, final_code, review_result),
            config={"run_name": RUN_CODE_REVISE, **_RUN_META},
        )
        review_result = parse_self_review(
            _self_review_chain.invoke(
                {"standards": standards, "code": final_code},
                config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
            )
        )
        final_score = review_result.score

    quality_note = build_quality_note(initial_score, final_score, len(review_result.issues))
    improved = extract_code(final_code)
    diff: str | None = generate_diff.invoke(
        {"original": base_code.strip(), "improved": improved}
    )
    return {"content": final_code + quality_note, "diff": diff, "generated_code": improved}


# ── Async streaming pipeline ──────────────────────────────────────────────────

async def _astream_generate_verified_code(
    review: str, request: str, raw_code: str, current_code: str = ""
):
    """Async generator that streams the final verified code token by token.

    Passes 1-4 (generate, self-review, revise, verify) run silently so only one
    clean code block is streamed. If a second revision is needed (rare), it is
    streamed live.
    """
    base_code = current_code if current_code else raw_code
    standards = retrieve_standards(request)

    # Pass 1: Generate (silent)
    generated: str = await _generate_chain.ainvoke(
        {"standards": standards, "review": review, "request": request, "current_code": base_code},
        config={"run_name": RUN_CODE_GENERATE, **_RUN_META},
    )

    # Pass 2: Self-review (silent)
    review_result = parse_self_review(
        await _self_review_chain.ainvoke(
            {"standards": standards, "code": generated},
            config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
        )
    )
    initial_score: int = review_result.score
    final_score = initial_score

    if initial_score >= PERFECT_SCORE:
        # Already perfect — stream the generated code directly
        yield {"type": "token", "content": generated}
        final_code = generated
    else:
        # Pass 3: Revision 1 (silent)
        rev1: str = await _revision_chain.ainvoke(
            _revision_inputs(standards, generated, review_result),
            config={"run_name": RUN_CODE_REVISE, **_RUN_META},
        )

        # Pass 4: Verify revision 1 (silent)
        review_result = parse_self_review(
            await _self_review_chain.ainvoke(
                {"standards": standards, "code": rev1},
                config={"run_name": RUN_CODE_REVIEW, **_RUN_META},
            )
        )
        final_score = review_result.score

        if final_score >= PERFECT_SCORE:
            # Revision 1 is verified 10/10 — stream it
            yield {"type": "token", "content": rev1}
            final_code = rev1
        else:
            # Pass 5: Revision 2 — stream this final attempt live
            rev2_chunks: list[str] = []
            async for chunk in _revision_chain.astream(
                _revision_inputs(standards, rev1, review_result),
                config={"run_name": RUN_CODE_REVISE, **_RUN_META},
            ):
                rev2_chunks.append(chunk)
                yield {"type": "token", "content": chunk}
            final_code = "".join(rev2_chunks)

    yield {"type": "token", "content": build_quality_note(initial_score, final_score, len(review_result.issues))}

    improved = extract_code(final_code)
    diff: str | None = generate_diff.invoke(
        {"original": base_code.strip(), "improved": improved}
    )
    yield {"type": "done", "diff": diff, "generated_code": improved}


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
        {"review": review, "user_message": question, "ai_response": full_response},
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
        {"review": review, "user_message": question, "ai_response": chat_answer},
        config={"run_name": RUN_CHAT_AGENT, **_RUN_META},
    )
    should_update, new_score, _ = parse_score_recheck(recheck_raw)
    updated_review: str | None = update_review_score(review, new_score) if should_update else None

    return {"content": chat_answer, "diff": None, "generated_code": None, "updated_review": updated_review}

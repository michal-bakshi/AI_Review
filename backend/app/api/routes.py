"""FastAPI route definitions for the AI Code Review API.

  POST /review/start/stream         — stream the review token by token (SSE)
  POST /review/start                — run the full graph and return the final review
  POST /review/{id}/chat/stream     — stream a follow-up answer token by token (SSE)
  POST /review/{id}/chat            — answer a follow-up question about the review

Route handlers are intentionally thin: they own only HTTP concerns
(thread-id generation, SSE formatting, HTTPException mapping).
All business logic lives in ReviewService.
"""

import asyncio
import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatRequest, ChatResponse, ReviewRequest, ReviewStartResponse
from app.api.service import ReviewService
from app.core.logging import logger
from app.graph.workflow import workflow

router = APIRouter(prefix="/review", tags=["review"])
service = ReviewService(workflow)


# ── SSE helpers ────────────────────────────────────────────────────────────────


def _sse(data: dict) -> str:
    """Serialise a dict as a single Server-Sent Event data line."""
    return f"data: {json.dumps(data)}\n\n"


async def _to_sse(source: AsyncIterator[dict]) -> AsyncIterator[str]:
    """Convert a dict-yielding async generator to SSE-formatted string chunks.
    Yields to the event loop after each chunk so the transport can flush (avoids
    buffering the whole stream and delivers token-by-token to the client).
    """
    async for event in source:
        yield _sse(event)
        await asyncio.sleep(0)


def _streaming_response(generator: AsyncIterator[str]) -> StreamingResponse:
    """Wrap an SSE string generator in a standard StreamingResponse."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Review endpoints ───────────────────────────────────────────────────────────


@router.post("/start/stream")
async def start_review_stream(payload: ReviewRequest) -> StreamingResponse:
    """Stream the code review token by token via SSE."""
    thread_id = str(uuid.uuid4())
    return _streaming_response(_to_sse(service.stream_review(payload.code, thread_id)))


@router.post("/start", response_model=ReviewStartResponse)
async def start_review(payload: ReviewRequest) -> ReviewStartResponse:
    """Run the full review pipeline and return the completed review."""
    thread_id = str(uuid.uuid4())
    try:
        return await service.run_review(payload.code, thread_id)
    except Exception as exc:
        logger.error("start_review failed for thread %s: %s", thread_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Chat endpoints ─────────────────────────────────────────────────────────────


@router.post("/{thread_id}/chat", response_model=ChatResponse)
async def chat(thread_id: str, payload: ChatRequest) -> ChatResponse:
    """Answer a follow-up question about a completed code review."""
    history = [msg.model_dump() for msg in payload.history]
    try:
        return service.answer_chat(
            thread_id, payload.question, history, current_code=payload.current_code or ""
        )
    except Exception as exc:
        logger.error("chat failed for thread %s: %s", thread_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{thread_id}/chat/stream")
async def chat_stream(thread_id: str, payload: ChatRequest) -> StreamingResponse:
    """Stream the answer to a follow-up question token by token via SSE."""
    history = [msg.model_dump() for msg in payload.history]
    try:
        final_review, raw_code = service.get_thread_context(thread_id)
    except (ValueError, RuntimeError) as exc:
        logger.error("chat_stream state lookup failed for thread %s: %s", thread_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return _streaming_response(
        _to_sse(
            service.stream_chat(
                thread_id,
                payload.question,
                history,
                final_review,
                raw_code,
                current_code=payload.current_code or "",
            )
        )
    )

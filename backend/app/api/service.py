"""Business-logic service for the code review API.

All pipeline orchestration lives here so route handlers stay thin.
Routes are responsible only for HTTP concerns (SSE formatting, error → HTTPException).
"""

from typing import AsyncIterator

from langgraph.graph.state import CompiledStateGraph

from app.agents.chat.chat_agent import answer_question, astream_answer
from app.agents.code_parser.code_parser import code_parser_node
from app.agents.rag_retrieval.rag_retrieval import rag_retrieval_node
from app.agents.review_writer.review_writer import astream_review_llm
from app.api.schemas import ChatResponse, ReviewStartResponse
from app.core.constants import DEFAULT_LANGUAGE, FALLBACK_STANDARDS
from app.core.logging import logger


class ReviewService:
    """Orchestrates the review and chat pipelines against a compiled LangGraph workflow."""

    def __init__(self, workflow: CompiledStateGraph) -> None:
        self._workflow = workflow

    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}

    # ── Non-streaming review ───────────────────────────────────────────────────

    async def run_review(self, code: str, thread_id: str) -> ReviewStartResponse:
        """Invoke the full graph and return the completed review."""
        result = await self._workflow.ainvoke(
            {"raw_code": code}, config=self._config(thread_id)
        )
        return ReviewStartResponse(
            thread_id=thread_id,
            final_review=result.get("final_review", ""),
            language=result.get("language", "unknown"),
        )

    # ── Streaming review ───────────────────────────────────────────────────────

    async def stream_review(
        self, code: str, thread_id: str
    ) -> AsyncIterator[dict]:
        """Yield event dicts as the review pipeline progresses phase by phase.

        Event shapes:
          {"type": "status",  "content": "parsing"|"retrieving"|"writing"}
          {"type": "token",   "content": "<text chunk>"}
          {"type": "done",    "thread_id": ..., "language": ..., "final_review": ...}
          {"type": "error",   "content": "<message>"}
        """
        config = self._config(thread_id)
        try:
            yield {"type": "status", "content": "parsing"}
            parser_result = code_parser_node({"raw_code": code})
            language: str = parser_result.get("language", DEFAULT_LANGUAGE)
            structure: dict = parser_result.get("parsed_structure", {})

            yield {"type": "status", "content": "retrieving"}
            rag_result = rag_retrieval_node(
                {"raw_code": code, "language": language, "parsed_structure": structure}
            )
            retrieved_docs: list[str] = rag_result.get("retrieved_docs", [])
            standards = "\n---\n".join(retrieved_docs) or FALLBACK_STANDARDS

            yield {"type": "status", "content": "writing"}
            review_chunks: list[str] = []
            async for chunk in astream_review_llm(language, structure, standards, code):
                review_chunks.append(chunk)
                yield {"type": "token", "content": chunk}

            final_review = "".join(review_chunks)

            self._workflow.update_state(
                config,
                {
                    "raw_code": code,
                    "language": language,
                    "parsed_structure": structure,
                    "retrieved_docs": retrieved_docs,
                    "final_review": final_review,
                    "error": parser_result.get("error") or rag_result.get("error"),
                },
            )
            yield {
                "type": "done",
                "thread_id": thread_id,
                "language": language,
                "final_review": final_review,
            }

        except (ValueError, RuntimeError, OSError) as exc:
            logger.error("stream_review operational error for thread %s: %s", thread_id, exc)
            yield {"type": "error", "content": str(exc)}
        except Exception as exc:
            logger.error("stream_review unexpected error for thread %s: %s", thread_id, exc)
            yield {"type": "error", "content": str(exc)}
            raise

    # ── Thread state ───────────────────────────────────────────────────────────

    def get_thread_context(self, thread_id: str) -> tuple[str, str]:
        """Return ``(final_review, raw_code)`` persisted for a completed review thread."""
        state = self._workflow.get_state(self._config(thread_id))
        return (
            state.values.get("final_review", ""),
            state.values.get("raw_code", ""),
        )

    # ── Non-streaming chat ─────────────────────────────────────────────────────

    def answer_chat(
        self,
        thread_id: str,
        question: str,
        history: list[dict],
        current_code: str = "",
    ) -> ChatResponse:
        """Answer a follow-up question synchronously."""
        final_review, raw_code = self.get_thread_context(thread_id)
        result = answer_question(
            review=final_review,
            question=question,
            history=history,
            raw_code=raw_code,
            current_code=current_code,
        )
        return ChatResponse(
            answer=result["content"],
            diff=result.get("diff"),
            updated_review=result.get("updated_review"),
        )

    # ── Streaming chat ─────────────────────────────────────────────────────────

    async def stream_chat(
        self,
        thread_id: str,
        question: str,
        history: list[dict],
        final_review: str,
        raw_code: str,
        current_code: str = "",
    ) -> AsyncIterator[dict]:
        """Yield event dicts as the chat answer streams token by token.

        ``final_review`` and ``raw_code`` are passed in directly so the caller
        can validate thread state before streaming starts (enabling an HTTP 500
        response instead of an in-stream error when the thread is missing).
        ``current_code`` is the code base for this generation — when the user asks
        to modify a previous AI fix, pass that fix so the diff reflects the delta.
        """
        try:
            async for chunk in astream_answer(
                review=final_review,
                question=question,
                history=history,
                raw_code=raw_code,
                current_code=current_code,
            ):
                yield chunk
        except (ValueError, RuntimeError, OSError) as exc:
            logger.error("stream_chat operational error for thread %s: %s", thread_id, exc)
            yield {"type": "error", "content": str(exc)}
        except Exception as exc:
            logger.error("stream_chat unexpected error for thread %s: %s", thread_id, exc)
            yield {"type": "error", "content": str(exc)}
            raise

"""Review writer node — generates a structured code review using LLM + RAG context."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.review_writer.prompts import REVIEW_PROMPT
from app.agents.review_writer.utils import format_retrieved_standards
from app.core.config import settings
from app.core.constants import AGENT_VERSION, DEFAULT_LANGUAGE, RUN_REVIEW_WRITER, TEMP_BALANCED
from app.graph.state import ReviewState

_llm = ChatOpenAI(model=settings.openai_model, temperature=TEMP_BALANCED)
_chain = ChatPromptTemplate.from_template(REVIEW_PROMPT) | _llm | StrOutputParser()

_RUN_CFG = {
    "run_name": RUN_REVIEW_WRITER,
    "metadata": {"project": settings.langchain_project, "version": AGENT_VERSION},
}


async def astream_review_llm(
    language: str, structure: dict, standards: str, code: str
):
    """Stream the review LLM token by token, yielding raw string chunks."""
    async for chunk in _chain.astream(
        {"language": language, "structure": structure, "standards": standards, "code": code},
        config=_RUN_CFG,
    ):
        yield chunk


def review_writer_node(state: ReviewState) -> dict:
    """Generate a structured markdown code review using the LLM.

    Combines parsed structure and RAG-retrieved standards into the prompt.
    Returns partial state with: final_review (and optionally error).
    """
    standards = format_retrieved_standards(state.get("retrieved_docs", []))

    try:
        review: str = _chain.invoke(
            {
                "language": state.get("language", DEFAULT_LANGUAGE),
                "structure": state.get("parsed_structure", {}),
                "standards": standards,
                "code": state["raw_code"],
            },
            config=_RUN_CFG,
        )
        return {"final_review": review}
    except Exception as exc:
        return {"final_review": "", "error": f"review_writer: {exc}"}

"""Review writer node — generates a structured code review using LLM + RAG context."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.review_writer.prompts import REVIEW_HUMAN, REVIEW_SYSTEM
from app.agents.review_writer.utils import format_retrieved_standards
from app.core.config import settings
from app.fine_tuning.collector import collect_review_example
from app.core.validation import validate_review, validate_review_async
from app.core.constants import (
    AGENT_VERSION,
    CODE_QUALITY_RULES,
    DEFAULT_LANGUAGE,
    LLM_TEMPERATURE,
    REVIEWER_GUIDELINES,
    RUN_REVIEW_WRITER,
)
from app.graph.state import ReviewState

_llm = ChatOpenAI(model=settings.openai_model, temperature=LLM_TEMPERATURE)
_chain = (
    ChatPromptTemplate.from_messages([("system", REVIEW_SYSTEM), ("human", REVIEW_HUMAN)])
    | _llm
    | StrOutputParser()
)

_RUN_CFG = {
    "run_name": RUN_REVIEW_WRITER,
    "metadata": {"project": settings.langchain_project, "version": AGENT_VERSION},
}


async def astream_review_llm(
    language: str, structure: dict, standards: str, code: str
):
    """Stream the review LLM token by token; after completion, validate with Gemini and yield the conservative review."""
    chain_input = {
        "language": language,
        "structure": structure,
        "standards": standards,
        "code": code,
        "guidelines": REVIEWER_GUIDELINES,
        "rules": CODE_QUALITY_RULES,
    }
    chunks: list[str] = []
    async for chunk in _chain.astream(chain_input, config=_RUN_CFG):
        chunks.append(chunk)
        yield chunk
    full_review = "".join(chunks)
    validated = await validate_review_async(chain_input, full_review, REVIEW_SYSTEM, REVIEW_HUMAN)
    system_content = REVIEW_SYSTEM.format(**chain_input)
    user_content = REVIEW_HUMAN.format(**chain_input)
    collect_review_example(system_content, user_content, validated)
    # Yield validated review as a special payload so the service can use it for state
    # without sending it again as a token (which would duplicate the text for the user).
    yield {"final_review": validated}


def review_writer_node(state: ReviewState) -> dict:
    """Generate a structured markdown code review using the LLM.

    Combines parsed structure and RAG-retrieved standards into the prompt.
    Returns partial state with: final_review (and optionally error).
    """
    standards = format_retrieved_standards(state.get("retrieved_docs", []))

    try:
        chain_input = {
            "language": state.get("language", DEFAULT_LANGUAGE),
            "structure": state.get("parsed_structure", {}),
            "standards": standards,
            "code": state["raw_code"],
            "guidelines": REVIEWER_GUIDELINES,
            "rules": CODE_QUALITY_RULES,
        }
        review: str = _chain.invoke(chain_input, config=_RUN_CFG)
        review = validate_review(chain_input, review, REVIEW_SYSTEM, REVIEW_HUMAN)
        system_content = REVIEW_SYSTEM.format(**chain_input)
        user_content = REVIEW_HUMAN.format(**chain_input)
        collect_review_example(system_content, user_content, review)
        return {"final_review": review}
    except Exception as exc:
        return {"final_review": "", "error": f"review_writer: {exc}"}

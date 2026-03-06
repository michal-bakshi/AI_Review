"""Code parser node — detects language and extracts structure from submitted code."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.code_parser.prompts import PARSE_PROMPT
from app.agents.code_parser.schemas import CodeAnalysisResult
from app.core.config import settings
from app.core.constants import AGENT_VERSION, DEFAULT_LANGUAGE, TEMP_PRECISE
from app.graph.state import ReviewState

_llm = ChatOpenAI(model=settings.openai_model, temperature=TEMP_PRECISE)
_chain = ChatPromptTemplate.from_template(PARSE_PROMPT) | _llm.with_structured_output(
    CodeAnalysisResult
)


def code_parser_node(state: ReviewState) -> dict:
    """Parse submitted code to detect language and extract its structure.

    Returns partial state with: language, parsed_structure (and optionally error).
    """
    try:
        result: CodeAnalysisResult = _chain.invoke(
            {"code": state["raw_code"]},
            config={
                "run_name": "code_parser",
                "metadata": {"project": settings.langchain_project, "version": AGENT_VERSION},
            },
        )
        return {
            "language": result.language or DEFAULT_LANGUAGE,
            "parsed_structure": result.model_dump(),
        }
    except Exception as exc:
        return {
            "language": DEFAULT_LANGUAGE,
            "parsed_structure": {
                "language": DEFAULT_LANGUAGE,
                "functions": [],
                "classes": [],
                "issues": [],
            },
            "error": f"code_parser: {exc}",
        }

"""Central constants for the AI Code Review Agent backend.

All magic numbers and fixed strings live here — nothing is hardcoded in agent files.
"""

# ── App metadata ───────────────────────────────────────────────────────────────
APP_TITLE       = "AI Code Review Agent"
APP_DESCRIPTION = "Multi-agent code review system powered by LangGraph, LangChain, and LangSmith."
APP_VERSION     = "1.0.0"
AGENT_VERSION   = "1.0"

# ── LLM temperatures ──────────────────────────────────────────────────────────
TEMP_PRECISE  = 0.0  # deterministic — intent classification, JSON output, self-review
TEMP_BALANCED = 0.2  # slight creativity — code generation, revision, review writing
TEMP_CHAT     = 0.3  # conversational — Q&A responses

# ── RAG retrieval ─────────────────────────────────────────────────────────────
RAG_K_REVIEW   = 4  # docs fetched during the review pipeline
RAG_K_CHAT     = 5  # docs fetched during chat code generation
RAG_MAX_ISSUES = 3  # max issues used to build the RAG query string

# ── Code generation quality gate ──────────────────────────────────────────────
PERFECT_SCORE      = 10  # self-review score that skips the revision pass
MAX_REVISION_PASSES = 2  # maximum number of revision attempts per generation

# ── LLM run names (used in LangSmith tracing) ─────────────────────────────────
RUN_INTENT_CHECK  = "intent_check"
RUN_CODE_GENERATE = "code_generate"
RUN_CODE_REVIEW   = "code_self_review"
RUN_CODE_REVISE   = "code_revise"
RUN_CHAT_AGENT    = "chat_agent"
RUN_REVIEW_WRITER = "review_writer"

# ── LangGraph node → frontend AgentStatus mapping ─────────────────────────────
NODE_STATUS_MAP: dict[str, str] = {
    "code_parser":    "parsing",
    "rag_retrieval":  "retrieving",
    "review_writer":  "writing",
}

# ── Quality-note templates ─────────────────────────────────────────────────────
QUALITY_NOTE_REVISED = (
    "\n\n---\n> **Quality check** — initial score **{initial}/{perfect}**; "
    "revised to fix {count} issue(s) → final score **{final}/{perfect}**."
)
QUALITY_NOTE_PERFECT = (
    "\n\n---\n> **Quality check** — scored **{perfect}/{perfect}**. "
    "No revision needed."
)

# ── Ingest ────────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50
INLINE_SOURCE = "inline_standards"

# ── Fallback / default strings ────────────────────────────────────────────────
DEFAULT_LANGUAGE   = "unknown"
DEFAULT_LANG_QUERY = "code"
FALLBACK_STANDARDS = "No specific standards were retrieved; apply general best practices."

# ── Shared code-quality rules ──────────────────────────────────────────────────
# Used verbatim in both the review prompt and the generation/self-review prompts
# so generated code is held to the exact same bar it would be reviewed against.
CODE_QUALITY_RULES = """\
- **Single Responsibility:** Each function does exactly one thing. If it does more, split it.
- **Readability:** Avoid complex expressions or non-obvious logic. \
Self-explanatory code needs no comments — do not add comments to obvious code.
- **Hardcoded values:** No magic numbers or hardcoded strings — extract them as named constants.
- **No unnecessary complexity:** Use the simplest correct approach; don't over-engineer.
- **No unused imports or variables:** Remove anything that isn't used.
- **Loop variables:** Declare variables outside a loop when they don't need to be inside it.
- **Syntax & Notation Errors:** Flag any syntax mistake or notation confusion \
(e.g. mixing up b′ vs d′, p vs q, ≤ vs ≥, = vs ==, or similar look-alike symbols). \
Each such error must reduce the score proportionally: one minor error ≈ −1 to −2 points; \
multiple or critical errors reduce more. A single notation mistake in an otherwise good \
function should not score below 6/10.\
"""


# - **Correctness:** No logical errors or unhandled edge cases that would cause wrong behaviour.

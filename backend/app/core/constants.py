"""Central constants for the AI Code Review Agent backend.

All magic numbers and fixed strings live here — nothing is hardcoded in agent files.
"""

# ── App metadata ───────────────────────────────────────────────────────────────
APP_TITLE       = "AI Code Review Agent"
APP_DESCRIPTION = "Multi-agent code review system powered by LangGraph, LangChain, and LangSmith."
APP_VERSION     = "1.0.0"
AGENT_VERSION   = "1.0"

# ── LLM temperature ───────────────────────────────────────────────────────────
LLM_TEMPERATURE = 0.0

# ── RAG retrieval ─────────────────────────────────────────────────────────────
RAG_K_DEFAULT = 4   # default number of docs to fetch; agents override when needed
RAG_K_CHAT     = 5  # chat code generation (override)
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
# General best practices shown when no language-specific standards were retrieved.
FALLBACK_STANDARDS = """\
General best practices (when no language-specific standards were retrieved):
- Single responsibility: each function does one thing; if it does more, split it.
- Clear naming: variables and functions should describe their purpose at a glance.
- No magic numbers: extract bare literals (e.g. 100, 3000, "admin") as named constants. \
array.length and similar are not magic numbers.
- Early returns: validate inputs early and return, reducing nesting and cognitive load.
- Explicit error handling: only for external I/O, network calls, or untrusted input.
- No dead code: remove unused imports, variables, and unreachable branches.
- Avoid deep nesting: more than two levels of indentation usually signals a refactor opportunity.\
"""

# ── Reviewer meta-guidelines ──────────────────────────────────────────────────
# How to apply the quality bar: when to give 10, scoring band, severity, and reviewer-only pitfalls.
REVIEWER_GUIDELINES = """\
- **Never flag variable/parameter placement:** Parameters are defined by the function signature — their position is never an issue. \
Variables declared at the top of a function are a valid style choice. \
Do NOT suggest moving anything "closer to its use". \
If placement is the only thing you notice, score 10/10 with no Key Improvements.
- **Give 10 when the code deserves it:** Correct, clear code with no real issues = **10/10**. \
Do NOT hunt for problems. Key Improvements may be "There are no meaningful issues" or empty.
- **Snippet context:** Code is a function/snippet only. Do NOT flag missing imports, class, or file structure.
- **Pitfalls:** Do NOT suggest `const` for variables that are reassigned (e.g. loop accumulators). \
Do NOT suggest moving variable declarations or parameters — parameters are part of the function \
signature and their position is never an issue. Short idiomatic names (arr, i, n, total) are fine — \
only flag naming when it is genuinely confusing; if names are clear, say nothing. At most **[Suggestion]**; \
never Critical or Important for naming.
- **Style:** Do not suggest rewriting clear code to a different idiom unless the review explicitly requires it \
(e.g. do not replace a for-loop with reduce, a class with a function, or sync code with async).
- **No comments:** Do not suggest adding comments or docstrings unless the review scope explicitly includes documentation.
- **Optional property:** Suggest fallback (e.g. `item.price ?? 0`) only for genuine optional/API data; at most one per function.
- **Severity:** Critical = logic/crash; Important = readability/maintainability; Suggestion = optional. \
Do NOT label micro-optimisation or variable placement as Important.
- **Scoring:** 10 = clean; 9 = one tiny polish; 7–8 = small improvements; 5–6 = readability/design; \
3–4 = logic errors; 1–2 = broken.\
- **Parameters are not variables to flag:** A parameter in the function signature is placed there by definition. 
  Do NOT flag a parameter's position, declaration, or proximity to its use. 
  It is not a variable placement issue — it is the function's interface.
"""

# ── Shared code-quality rules ──────────────────────────────────────────────────
# Single source for the review/generation bar; used by review writer, chat generate/revise/self-review.
CODE_QUALITY_RULES = """\
- **Simplicity first:** Use the simplest correct solution. Fewer lines, less nesting.
- **No comments or docs:** Do not add comments, docstrings, or JSDoc.
- **No tests:** Do not add test functions or assertions unless explicitly asked.
- **Single responsibility:** Suggest splitting only when one function clearly does two unrelated jobs. \
Do not flag validation-then-delegation as redundant.
- **Style:** Do not flag idiom choices (e.g. for-loop vs reduce, class vs function). \
Flag only when the chosen idiom causes a real readability or correctness issue.
- **Magic number (definition):** A numeric literal whose meaning is not obvious from context (e.g. 100, 3000, 24 for hours). \
Never flag 0, 1, or -1. Never flag array.length, .length, len, count, size, or loop bounds/indices. \
Flag only when the literal is domain-specific and a named constant would clearly help readability.
- **Hardcoded (definition):** A literal that represents config or environment-specific data (e.g. role names like "admin", API URLs, timeouts) that would change per environment. \
Not hardcoded: "", single characters, numbers 0/1/-1, format strings used once in context.
- **No unused imports or variables:** Remove anything not used.
- **No micro-optimisations:** Flag only correctness or real readability issues.
- **No variable placement:** Do not flag where variables or parameters are declared. \
  Parameters are part of the function signature — their position is never an issue. \
  FALSE POSITIVE — never flag: "parameter X could be moved closer to its use".
- **Error handling:** Suggest only for I/O, network, or untrusted input; never for pure logic (caller passes valid data).
- **Syntax & notation errors:** Flag mistakes; one minor error in otherwise good code: still ≥ 6/10.\
"""
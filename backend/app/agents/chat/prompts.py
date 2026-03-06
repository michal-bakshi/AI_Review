"""Prompt templates for the chat agent pipeline."""

from app.core.constants import CODE_QUALITY_RULES

INTENT_PROMPT = """Is the following message asking you to write, create, generate, \
fix, improve, refactor, or update code (a function, class, snippet, etc.)?

Message: {question}

Reply with a single word — YES or NO."""

CHAT_SYSTEM = """You are a helpful senior software engineer. You just produced the \
code review below and the developer has follow-up questions about it.

--- CODE REVIEW ---
{review}
--- END REVIEW ---

Answer clearly and concisely. Reference specific parts of the review where relevant. \
Use markdown for code snippets or lists where helpful."""

GENERATE_PROMPT = """You are a senior software engineer fixing and improving existing code.

CRITICAL — follow these rules before writing a single line:
1. You MUST start from the Code to Improve below — never write new code from scratch.
2. Keep every existing function name, class name, and variable name exactly as written.
3. Keep the overall structure and logic flow intact.
4. Apply only the minimum changes required to address the review feedback and the request.

## Code to Improve
```
{current_code}
```

## Code Review
{review}

## Coding Standards (retrieved from knowledge base)
{standards}

## Developer Request
{request}

Every rule below is non-negotiable — the same rules will be used to review your output:

{rules}

Additional rules — match complexity to the request:
- Simple functions: 1-line docstring is enough; no elaborate error handling
- Complex / multi-step logic: concise docstring with Args/Returns; handle realistic failures
- Type hints on all parameters and return values

Return ONLY the fixed code inside a markdown fenced code block with the language tag. \
No explanation, commentary, or design-decision notes outside the code block.""".replace(
    "{rules}", CODE_QUALITY_RULES
)

SELF_REVIEW_PROMPT = """You are a strict code reviewer. Score the code below from 1 to 10, \
where 10 means zero issues.

## Quality Rules (score against these — same rules used during generation)
{rules}

## Extra Coding Standards (from knowledge base)
{standards}

## Code to Review
{code}

Respond with ONLY valid JSON — no markdown fences, no extra text:
{{
  "score": <integer 1-10>,
  "issues": ["<concise description of issue>", ...],
  "suggestions": ["<specific, actionable improvement>", ...]
}}""".replace("{rules}", CODE_QUALITY_RULES)

REVISION_PROMPT = """Revise the code below to fix every issue listed and achieve a 10/10 quality score.

CRITICAL — apply ONLY the changes needed to fix the listed issues. Do not rename, \
restructure, or rewrite anything that is not explicitly listed as an issue.

## Quality Rules (the same rules will be used to verify your output)
{rules}

## Coding Standards
{standards}

## Code to Revise
{code}

## Issues to Fix
{issues}

## Required Improvements
{suggestions}

Return ONLY the revised code inside a markdown fenced code block with the language tag. \
No explanation outside the code block.""".replace("{rules}", CODE_QUALITY_RULES)

SCORE_RECHECK_PROMPT = """A developer received the code review below and sent a follow-up \
message, which you answered. Determine if the review score should be updated.

## Code Review
{review}

## Developer's Message
{user_message}

## Your Response
{ai_response}

Should the score in the review be updated? Update ONLY if ALL of the following are true:
1. The developer explicitly argued that a specific part of their code is better than the review suggests.
2. Your response shows clear technical agreement with their argument (not just acknowledging it).
3. The new score would be strictly higher than the current score.

Reply with ONLY valid JSON, no other text:
{{"update": false}}
OR
{{"update": true, "new_score": <integer 1-10>, "reason": "<one concise sentence>"}}"""

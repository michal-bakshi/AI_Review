"""Prompt templates for the code parser agent."""

# Extracts language, functions, classes, and quality-issue phrases from code for RAG retrieval.
PARSE_SYSTEM = """You are a code analysis expert. Extract structured data from the submitted code.

## Output
- **Language:** The programming language.
- **Functions/methods:** All function and method names.
- **Classes:** All class names.
- **Issues:** Code quality issues as short, searchable phrases for RAG retrieval.

## Issue extraction
Only list issues that actually appear in the code. Do not guess or invent.
- Do NOT list: 0, 1, -1 as magic numbers; array.length/len/count/size; comments/docs; variable placement; loop counters (i, j, k).
- Good examples: "magic number 100 in condition", "unused variable x", "function does multiple things", "missing error handling on file I/O", "hardcoded string constant", "deeply nested conditionals", "duplicated logic"."""

PARSE_HUMAN = """Code:
{code}"""

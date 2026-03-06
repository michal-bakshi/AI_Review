"""Prompt templates for the code parser agent."""

PARSE_PROMPT = """You are a code analysis expert. Analyze the following code and extract:
- The programming language
- All function and method names
- All class names
- Any potential code quality issues

Code:
{code}"""

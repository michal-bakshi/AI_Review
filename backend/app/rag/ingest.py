"""One-time ingestion script — populates ChromaDB with coding standards documentation.

Run from the backend/ directory before starting the server:
    python -m app.rag.ingest
"""

import sys
import os

from dotenv import load_dotenv

# Allow running as a script from the backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load .env before any app imports so os.environ is populated for OpenAI clients
load_dotenv()

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

from app.core.constants import CHUNK_OVERLAP, CHUNK_SIZE, INLINE_SOURCE
from app.core.logging import logger
from app.rag.vectorstore import get_vectorstore

INGEST_BATCH_SIZE = 100

DOCUMENTATION_URLS = [
    "https://peps.python.org/pep-0008/",
    "https://google.github.io/styleguide/pyguide.html",
    "https://google.github.io/styleguide/tsguide.html",
    "https://google.github.io/styleguide/javaguide.html",
]

INLINE_STANDARDS = """
Python Best Practices:
- Use type hints for all function parameters and return types: def add(a: int, b: int) -> int
- Missing type hints on parameters make code harder to understand and IDE support weaker
- Keep functions small and single-purpose (fewer than 30 lines); split when they do multiple things
- Write docstrings for all public modules, classes, and functions explaining purpose and args
- Use meaningful variable names that describe their content and purpose
- Handle exceptions explicitly; never silently swallow errors with bare except clauses
- Use list comprehensions instead of map/filter where it improves readability
- Prefer f-strings over .format() or % formatting for string interpolation
- Use context managers (with statements) for file I/O and resource management
- Avoid mutable default arguments in function signatures (use None and initialise inside)
- Magic numbers: replace raw numeric literals with named constants (MAX_RETRIES = 3)
- Early returns: validate inputs at the top of a function to avoid deep nesting
- Single responsibility: a function that fetches data AND transforms AND saves it should be split

Python — Common Mistakes:
- Mutable default argument: def foo(items=[]) mutates across calls; use def foo(items=None) instead
- Shadowing builtins: avoid naming variables list, dict, id, type, input, etc.
- Missing error handling on file I/O: always wrap open() and network calls in try/except
- Deeply nested conditionals: more than 2 levels is a signal to extract a helper function
- Unused variables and imports increase cognitive load and should be removed

JavaScript and TypeScript Best Practices:
- Use const by default; use let only when reassignment is needed; never use var
- Prefer arrow functions for callbacks: array.map(item => item.id)
- Use async/await over raw Promise chains for cleaner asynchronous code
- Type all function parameters and return values in TypeScript: function greet(name: string): string
- Missing type annotations make TypeScript lose its main benefit — type safety
- Use optional chaining (?.) and nullish coalescing (??) to handle null/undefined safely
- Avoid the any type; use unknown for truly unknown values and narrow with type guards
- Keep React components small and focused on a single visual responsibility
- Use custom hooks to encapsulate reusable stateful logic out of components
- Handle loading, error, and empty states explicitly — never render undefined silently
- Always use strict equality (===) instead of loose equality (==)
- Hardcoded strings and magic numbers in JSX or logic should be extracted as constants

TypeScript — Common Mistakes:
- Using any disables type checking; prefer unknown with a type guard instead
- Not handling Promise rejections leads to unhandled rejection errors in production
- Mutating props or state directly bypasses React's rendering model
- Missing null checks before accessing nested object properties causes runtime crashes

General Clean Code Principles:
- DRY (Don't Repeat Yourself): extract duplicated logic into shared utilities or helpers
- Single Responsibility Principle: one module, one reason to change
- Fail fast: validate inputs early and raise meaningful, descriptive errors immediately
- Document the "why", not the "what" — code explains itself, comments explain intent
- Keep cyclomatic complexity low by avoiding deeply nested conditionals
- Use early returns to reduce indentation and improve readability
- Magic numbers and hardcoded strings are a maintenance risk — always use named constants
- Unused code (dead imports, unreachable branches) adds noise and should be deleted
- Variable declared inside a loop when it could be outside wastes allocation and is misleading
- Function does multiple things: fetch + transform + save should each be separate functions

Security Best Practices:
- Never hardcode credentials, API keys, or secrets — use environment variables
- Validate and sanitise all user input before processing or storing it
- Use parameterised queries or ORM methods; never concatenate SQL strings with user data
- Avoid exposing internal stack traces or error details to end users
"""


def _add_in_batches(vectorstore, chunks: list) -> None:
    """Add document chunks to the vectorstore in fixed-size batches.

    ChromaDB has a maximum batch size per upsert call. Splitting into smaller
    batches prevents 'Batch size exceeds maximum' errors on large documents.
    """
    for i in range(0, len(chunks), INGEST_BATCH_SIZE):
        vectorstore.add_documents(chunks[i : i + INGEST_BATCH_SIZE])


def ingest_inline_docs() -> None:
    """Chunk and embed the inline coding standards into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    doc = Document(page_content=INLINE_STANDARDS, metadata={"source": INLINE_SOURCE})
    chunks = splitter.split_documents([doc])

    vectorstore = get_vectorstore()
    _add_in_batches(vectorstore, chunks)
    logger.info(f"Ingested {len(chunks)} chunks from inline standards.")


def ingest_web_docs() -> None:
    """Attempt to ingest coding standards from external documentation URLs."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    for url in DOCUMENTATION_URLS:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            chunks = splitter.split_documents(docs)
            vectorstore = get_vectorstore()
            _add_in_batches(vectorstore, chunks)
            logger.info(f"Ingested {len(chunks)} chunks from {url}")
        except Exception as exc:
            logger.warning(f"Could not load {url}: {exc}")


if __name__ == "__main__":
    logger.info("Starting documentation ingestion...")
    ingest_inline_docs()
    ingest_web_docs()
    logger.info("Ingestion complete. ChromaDB is ready.")

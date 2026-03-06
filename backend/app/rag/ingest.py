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

DOCUMENTATION_URLS = [
    "https://peps.python.org/pep-0008/",
    "https://google.github.io/styleguide/pyguide.html",
]

INLINE_STANDARDS = """
Python Best Practices:
- Use type hints for all function signatures and return types
- Keep functions small and single-purpose (fewer than 30 lines)
- Write docstrings for all public modules, classes, and functions
- Use meaningful variable names that describe their purpose
- Handle exceptions explicitly; never silently swallow errors
- Use list comprehensions instead of map/filter where readable
- Prefer f-strings over .format() or % formatting
- Use context managers (with statements) for resource management
- Avoid mutable default arguments in function signatures
- Prefer dependency injection over global state

JavaScript / TypeScript Best Practices:
- Use const by default; let only when reassignment is needed; never var
- Prefer arrow functions for callbacks and functional patterns
- Use async/await over raw Promise chains for readability
- Type all function parameters and return values in TypeScript
- Use optional chaining (?.) and nullish coalescing (??) operators
- Avoid the any type; use unknown for truly unknown values
- Keep components small and focused on a single responsibility
- Use custom hooks to encapsulate reusable stateful logic
- Handle loading, error, and empty states visually in UI components
- Always use strict equality (===) instead of loose equality (==)

General Clean Code Principles:
- DRY: extract duplicated logic into shared utilities or helpers
- SOLID: single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- Fail fast: validate inputs early and raise meaningful, descriptive errors
- Use Conventional Commits for commit messages (feat:, fix:, chore:, docs:)
- Document the "why", not the "what" — code explains itself, comments explain intent
- Keep cyclomatic complexity low by avoiding deeply nested conditionals
- Use early returns to reduce indentation and improve readability
- Write tests for every public function and API endpoint
"""


def ingest_inline_docs() -> None:
    """Chunk and embed the inline coding standards into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    doc = Document(page_content=INLINE_STANDARDS, metadata={"source": INLINE_SOURCE})
    chunks = splitter.split_documents([doc])

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
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
            vectorstore.add_documents(chunks)
            logger.info(f"Ingested {len(chunks)} chunks from {url}")
        except Exception as exc:
            logger.warning(f"Could not load {url}: {exc}")


if __name__ == "__main__":
    logger.info("Starting documentation ingestion...")
    ingest_inline_docs()
    ingest_web_docs()
    logger.info("Ingestion complete. ChromaDB is ready.")

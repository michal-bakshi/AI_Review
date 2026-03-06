"""ChromaDB vector store — provides a reusable Chroma instance for retrieval."""

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

def get_vectorstore() -> Chroma:
    """Return a Chroma vectorstore connected to the configured persist directory."""
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_directory,
    )

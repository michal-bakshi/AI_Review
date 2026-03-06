"""Application configuration loaded from environment variables via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is sourced from environment variables or a .env file."""

    openai_api_key: str
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    langchain_project: str = "ai-code-review-agent"
    chroma_persist_directory: str = "./chroma_db"
    openai_model: str = "gpt-4o"

    # Embeddings
    embedding_model: str = "text-embedding-3-small"
    chroma_collection_name: str = "coding_standards"

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # SSE streaming
    sse_word_delay: float = 0.04

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

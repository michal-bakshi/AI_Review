"""FastAPI application entry point.

Start the server with:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.routes import router  # noqa: E402 — must be after load_dotenv
from app.core.config import settings  # noqa: E402
from app.core.constants import APP_DESCRIPTION, APP_TITLE, APP_VERSION  # noqa: E402
from app.core.logging import logger  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Code Review Agent starting up...")
    yield
    logger.info("AI Code Review Agent shutting down.")


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Liveness probe — confirms the API is running."""
    return {"status": "healthy", "version": APP_VERSION}

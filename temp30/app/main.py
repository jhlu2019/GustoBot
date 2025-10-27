from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.routes import router as api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Knowledge Ingestion Service",
        version="0.1.0",
        description="Rewrite tabular data with LLMs, embed via pgvector, and expose retrieval APIs.",
    )
    app.include_router(api_router, prefix="/api")

    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    logger.info("FastAPI application initialised")
    return app


app = create_app()

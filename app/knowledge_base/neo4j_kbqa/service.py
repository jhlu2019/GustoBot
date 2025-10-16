"""
High level service exposing graph and QA operations backed by Neo4j.
"""
from __future__ import annotations

import atexit
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.config import settings

from .database import Neo4jDatabase
from .graph_loader import GraphCache, convert_graph
from .pipeline import Neo4jQAPipeline


class Neo4jQAService:
    def __init__(self) -> None:
        driver_kwargs = {}
        if settings.NEO4J_MAX_CONNECTION_LIFETIME:
            driver_kwargs["max_connection_lifetime"] = settings.NEO4J_MAX_CONNECTION_LIFETIME

        self._database = Neo4jDatabase(
            settings.NEO4J_URI,
            settings.NEO4J_USER,
            settings.NEO4J_PASSWORD,
            **driver_kwargs,
        )
        self._pipeline = Neo4jQAPipeline(self._database)
        self._cache = GraphCache(Path(settings.NEO4J_GRAPH_CACHE_PATH))
        atexit.register(self.close)

    def close(self) -> None:
        try:
            self._database.close()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.warning(f"Failed to close Neo4j driver: {exc}")

    def get_default_graph(self, refresh: bool = False) -> Dict[str, Any]:
        if not refresh:
            cached = self._cache.load()
            if cached:
                return cached

        graph = self._database.fetch_graph(settings.NEO4J_DEFAULT_GRAPH_QUERY)
        payload = convert_graph(graph)
        self._cache.save(payload)
        return payload

    def ask(self, question: str) -> Dict[str, Any]:
        return self._pipeline.ask(question)


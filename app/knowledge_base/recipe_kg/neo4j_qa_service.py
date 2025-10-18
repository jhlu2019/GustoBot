"""
High level service exposing graph and QA operations backed by Neo4j.
"""
from __future__ import annotations

import atexit
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.config import settings

from .graph_database_client import Neo4jDatabase
from .graph_cache_loader import GraphCache, convert_graph
from .graph_importer_service import RecipeGraphImporter
from .qa_pipeline_orchestrator import Neo4jQAPipeline


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
        self._cache = GraphCache(Path(settings.NEO4J_GRAPH_CACHE_PATH))
        self._bootstrap_graph()
        self._pipeline = Neo4jQAPipeline(self._database)
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

    def _bootstrap_graph(self) -> None:
        if not settings.NEO4J_BOOTSTRAP_JSON:
            return

        recipe_path = Path(settings.NEO4J_RECIPE_JSON_PATH)
        ingredient_path = (
            Path(settings.NEO4J_INGREDIENT_JSON_PATH)
            if settings.NEO4J_INGREDIENT_JSON_PATH
            else None
        )

        importer = RecipeGraphImporter(self._database)
        try:
            imported = importer.bootstrap_from_json(
                recipe_path,
                ingredient_path,
                force=settings.NEO4J_BOOTSTRAP_FORCE,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to bootstrap Neo4j from JSON: {exc}")
            return

        if imported:
            self._cache.invalidate()

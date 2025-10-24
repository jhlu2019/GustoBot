"""Simple reranker integration for the knowledge base search pipeline."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from loguru import logger

from app.config import settings


class Reranker:
    """Optional reranker; currently supports Cohere's rerank endpoint."""

    def __init__(self) -> None:
        self.provider = settings.RERANKER_PROVIDER.lower() if settings.RERANKER_PROVIDER else None
        self.api_key = settings.RERANKER_API_KEY
        self.model = settings.RERANKER_MODEL or "rerank-english-v3.0"

        self.enabled = bool(self.provider and self.api_key)
        if self.enabled and self.provider != "cohere":
            logger.warning("Reranker provider %s not supported; fallback to disabled state.", self.provider)
            self.enabled = False

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not self.enabled or not documents:
            return documents[:top_k]

        try:
            ranked = await asyncio.to_thread(self._cohere_rerank, query, documents, top_k)
            if ranked:
                return ranked
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Reranker failed: %s", exc)
        return documents[:top_k]

    def _cohere_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        try:
            from cohere import Client as CohereClient
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("cohere package not installed") from exc

        client = CohereClient(self.api_key)
        inputs = [doc.get("content") or doc.get("document") or "" for doc in documents]
        response = client.rerank(
            query=query,
            documents=inputs,
            top_n=min(top_k, len(documents)),
            model=self.model,
        )

        order: List[Dict[str, any]] = []
        for item in response.results:
            idx = getattr(item, "index", None)
            if idx is None or idx >= len(documents):
                continue
            reranked_doc = dict(documents[idx])
            score = getattr(item, "relevance_score", None)
            if score is not None:
                reranked_doc["rerank_score"] = float(score)
            order.append(reranked_doc)

        # Append leftovers in their original order if rerank didn't include them
        seen = {doc.get("chunk_id") or doc.get("id") for doc in order}
        for doc in documents:
            identifier = doc.get("chunk_id") or doc.get("id")
            if identifier not in seen:
                order.append(doc)
        return order[:top_k]

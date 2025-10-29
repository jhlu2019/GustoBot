"""
Embedding helpers for the knowledge base module.

Provides a simple OpenAI-compatible embedding client that can talk to OpenAI,
DashScope (Qwen), or any service that exposes the compatible `/embeddings`
endpoint. We intentionally avoid depending on LangChain abstractions here so
that we can fine-tune the request payload for vendors that only support a
subset of OpenAI parameters (e.g., DashScope).
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from loguru import logger
from openai import OpenAI


class OpenAICompatibleEmbeddings:
    """Thin wrapper around the official OpenAI client for embedding requests."""

    def __init__(
        self,
        *,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        dimension: Optional[int] = None,
        max_batch_size: int = 64,
        request_timeout: Optional[float] = 60.0,
    ) -> None:
        self.model = model
        self.dimension = dimension
        self.max_batch_size = max_batch_size
        self.request_timeout = request_timeout

        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = OpenAI(**client_kwargs)
        logger.info(
            "Initialised OpenAI-compatible embeddings client (model=%s, base_url=%s)",
            model,
            base_url or "https://api.openai.com/v1",
        )

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed a sequence of texts."""
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        embeddings = self._embed([text])
        return embeddings[0] if embeddings else []

    def _embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []

        ordered_inputs: List[str] = []
        index_map: List[int] = []
        for idx, text in enumerate(texts):
            value = (text or "").strip()
            if not value:
                # DashScope 对空字符串会报错，使用单空格保持顺序
                value = " "
            ordered_inputs.append(value)
            index_map.append(idx)

        embeddings_flat: List[List[float]] = []
        try:
            for start in range(0, len(ordered_inputs), self.max_batch_size):
                batch = ordered_inputs[start:start + self.max_batch_size]
                response = self._client.embeddings.create(
                    model=self.model,
                    input=batch,
                    timeout=self.request_timeout,
                )

                for item in response.data:
                    vector = list(item.embedding)
                    if self.dimension and len(vector) != self.dimension:
                        logger.warning(
                            "Embedding dimension mismatch: expected=%s actual=%s",
                            self.dimension,
                            len(vector),
                        )
                    embeddings_flat.append(vector)

        except Exception as exc:  # pragma: no cover - surface upstream
            logger.exception("Embedding request failed: %s", exc)
            raise

        if len(embeddings_flat) != len(ordered_inputs):
            logger.error(
                "Embedding count mismatch (expected %s, received %s)",
                len(ordered_inputs),
                len(embeddings_flat),
            )
            raise RuntimeError("Embedding API returned unexpected number of vectors")

        result: List[List[float]] = [[] for _ in texts]
        for mapped_idx, vector in zip(index_map, embeddings_flat):
            result[mapped_idx] = vector

        if any(not vec for vec in result):
            fallback_dim = len(embeddings_flat[0]) if embeddings_flat else (self.dimension or 0)
            zero_vec = [0.0] * fallback_dim
            for idx, vec in enumerate(result):
                if not vec:
                    result[idx] = zero_vec

        return result

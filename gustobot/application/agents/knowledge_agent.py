"""
Thin wrapper around the knowledge retrieval service.

The production stack orchestrates retrieval via LangGraph workflows. For
unit testing and simplified deployments we keep this helper agent that
delegates to :class:`gustobot.infrastructure.knowledge.KnowledgeService`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from gustobot.infrastructure.knowledge import KnowledgeService


@dataclass
class KnowledgeResponse:
    """Normalized payload returned after a knowledge-base lookup."""

    answer: str
    sources: List[str]
    metadata: Dict[str, Any]


class KnowledgeAgent:
    """Wrapper that encapsulates access to the vector knowledge base."""

    name: str = "KnowledgeAgent"
    description: str = "Retrieve structured culinary knowledge from the vector store."

    def __init__(self, service: Optional['KnowledgeService'] = None) -> None:
        if service is not None:
            self.service = service
            self._import_error = None
        else:
            try:
                from gustobot.infrastructure.knowledge import KnowledgeService as _KnowledgeService  # local import to avoid heavy deps at import time
            except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
                self.service = None
                self._import_error = exc
            else:
                self.service = _KnowledgeService()
                self._import_error = None

    async def query(self, question: str, *, top_k: int = 5) -> KnowledgeResponse:
        if not question or not question.strip():
            return KnowledgeResponse(answer="", sources=[], metadata={"reason": "empty_question"})

        if self.service is None:
            raise RuntimeError(
                "KnowledgeService dependency is not available. "
                "Install the optional vector store dependencies or provide a stub service."
            ) from getattr(self, "_import_error", None)

        results = await self.service.search(question, top_k=top_k)
        if not results:
            return KnowledgeResponse(
                answer="抱歉，知识库中暂时没有找到相关内容。",
                sources=[],
                metadata={"reason": "no_results"},
            )

        top_result = results[0]
        sources = [
            str(item.get("source") or item.get("metadata", {}).get("source") or "")
            for item in results
            if item
        ]
        metadata = {
            "score": top_result.get("score"),
            "chunk_id": top_result.get("chunk_id") or top_result.get("id"),
        }
        return KnowledgeResponse(
            answer=top_result.get("content") or top_result.get("document") or "",
            sources=[source for source in sources if source],
            metadata=metadata,
        )

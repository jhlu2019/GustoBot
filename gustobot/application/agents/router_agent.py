"""
Heuristic router agent for classifying incoming user queries.

The implementation is intentionally lightweight and dependency free so it can
serve both as a default routing strategy in non-LLM environments and a
deterministic fallback when an upstream model cannot be reached.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal


Route = Literal["knowledge", "chat", "reject"]


@dataclass
class RouterResult:
    """Structured output returned by the router."""

    route: Route
    confidence: float
    reason: str


class RouterAgent:
    """
    Minimal rule-based router used throughout tests and small deployments.

    The heuristics are deliberately simple—production deployments are expected
    to swap this implementation with an LLM-backed classifier. Keeping the
    class self-contained avoids import cycles with LangGraph workflows.
    """

    name: str = "RouterAgent"
    description: str = "Route user messages to knowledge, chat, or reject handlers."

    _knowledge_keywords = {
        "怎么做",
        "如何做",
        "做法",
        "食谱",
        "菜谱",
        "配方",
        "步骤",
        "recipe",
        "cook",
        "ingredient",
    }
    _reject_keywords = {"违法", "违法", "违规", "非法", "不合法", "毒药"}

    def _rule_based_classification(self, message: str) -> Dict[str, str | float]:
        """
        Fast heuristic classifier used by unit tests.

        Returns
        -------
        dict
            route: Literal["knowledge", "chat", "reject"]
            confidence: float in [0, 1]
            reason: short textual explanation
        """
        if not message or not message.strip():
            return {
                "route": "chat",
                "confidence": 0.2,
                "reason": "No content supplied; default to chat.",
            }

        text = message.strip().lower()

        if any(word in text for word in self._reject_keywords):
            return {
                "route": "reject",
                "confidence": 0.95,
                "reason": "Message contains blacklisted vocabulary.",
            }

        if any(keyword in text for keyword in self._knowledge_keywords):
            return {
                "route": "knowledge",
                "confidence": 0.85,
                "reason": "Detected cooking or recipe intent.",
            }

        greetings = {"你好", "您好", "hi", "hello", "hey"}
        if any(text.startswith(greet) for greet in greetings):
            return {
                "route": "chat",
                "confidence": 0.65,
                "reason": "Greeting detected; routed to chat.",
            }

        return {
            "route": "knowledge",
            "confidence": 0.5,
            "reason": "Defaulted to knowledge due to lack of strong signals.",
        }

    def classify(self, message: str) -> RouterResult:
        """Public entry point returning a dataclass for convenience."""
        result = self._rule_based_classification(message)
        return RouterResult(
            route=result["route"],  # type: ignore[arg-type]
            confidence=float(result["confidence"]),
            reason=str(result["reason"]),
        )


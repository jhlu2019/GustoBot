"""
Simple template-driven chat agent used as a warm fallback.

The real system leverages LLMs for open conversations; this implementation
ensures we have deterministic behaviour for tests and environments where an
LLM is not configured.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ChatResponse:
    """Structured data returned by the chat agent."""

    message: str
    intent: str


class ChatAgent:
    """Template-based chat responder."""

    name: str = "ChatAgent"
    description: str = "Provide lightweight conversational replies without hitting an LLM."

    _templates: Dict[str, str] = {
        "greeting": (
            "你好！我是 GustoBot，很高兴为你提供菜谱和烹饪建议。"
            "如果你想了解某道菜的做法，可以告诉我菜名或者食材。"
        ),
        "thanks": "不用客气！如果还想了解其他菜谱或烹饪技巧，随时告诉我～",
        "fallback": "我在这里随时为你提供菜谱和烹饪相关的帮助，有任何问题都可以问我哦！",
    }

    def _detect_intent(self, message: str) -> str:
        msg = (message or "").strip().lower()
        if not msg:
            return "fallback"
        if any(keyword in msg for keyword in {"你好", "您好", "hello", "hi", "hey"}):
            return "greeting"
        if any(keyword in msg for keyword in {"谢谢", "thx", "thanks"}):
            return "thanks"
        return "fallback"

    def _generate_template_response(self, message: str) -> str:
        intent = self._detect_intent(message)
        return self._templates.get(intent, self._templates["fallback"])

    def respond(self, message: str) -> ChatResponse:
        """Return a structured chat response."""
        intent = self._detect_intent(message)
        return ChatResponse(
            message=self._templates.get(intent, self._templates["fallback"]),
            intent=intent,
        )


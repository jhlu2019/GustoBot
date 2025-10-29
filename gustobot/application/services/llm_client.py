"""
Lightweight wrapper for OpenAI-compatible chat completions.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger
from openai import AsyncOpenAI
from gustobot.config import settings

ChatMessage = Dict[str, str]


class LLMClient:
    """Async helper around chat completions."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_API_BASE or "").rstrip("/") or None
        self.model = model or settings.OPENAI_MODEL
        self.default_temperature = temperature

        self._client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,

            )
        else:
            logger.warning("LLMClient initialised without OPENAI_API_KEY; LLM features disabled.")

    def _ensure_client(self) -> AsyncOpenAI:
        if not self._client:
            raise RuntimeError("LLM client is not configured. Provide OPENAI_API_KEY to enable it.")
        return self._client

    @staticmethod
    def _format_messages(
        system_prompt: Optional[str],
        user_message: str,
        context: Optional[Sequence[ChatMessage]] = None,
    ) -> List[ChatMessage]:
        messages: List[ChatMessage] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context:
            for item in context:
                role = item.get("role")
                content = item.get("content")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})
        return messages

    async def complete(self, *, messages: Sequence[ChatMessage], **kwargs: Any):
        """Call the chat completion endpoint."""
        client = self._ensure_client()
        return await client.chat.completions.create(
            model=self.model,
            messages=list(messages),
            **kwargs,
        )

    async def chat(
        self,
        *,
        system_prompt: Optional[str],
        user_message: str,
        context: Optional[Sequence[ChatMessage]] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Return the assistant message content."""
        messages = self._format_messages(system_prompt, user_message, context)
        response = await self.complete(
            messages=messages,
            temperature=temperature if temperature is not None else self.default_temperature,
        )
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", "") if message else ""
        return content or ""

    async def chat_json(
        self,
        *,
        system_prompt: Optional[str],
        user_message: str,
        context: Optional[Sequence[ChatMessage]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Request a JSON object response and parse it."""
        messages = self._format_messages(system_prompt, user_message, context)
        try:
            response = await self.complete(
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("Structured response failed ({}); falling back to plain text.", exc)
            response = await self.complete(messages=messages, temperature=temperature)
            content = response.choices[0].message.content or ""

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response: {}", content)
            return {}

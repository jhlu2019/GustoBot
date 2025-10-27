from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional

import requests
from openai import OpenAI

from app.core.config import Config

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    QWEN = "qwen"
    OLLAMA = "ollama"
    GLM = "glm"


class LLMClient:
    """Provider-agnostic interface for generating rewritten text."""

    def __init__(self, config: Config):
        self.config = config
        self.provider = LLMProvider(config.llm_provider.lower())
        self._setup_client()

    def _setup_client(self) -> None:
        if self.provider in (LLMProvider.OPENAI, LLMProvider.QWEN):
            api_key = self.config.llm_api_key or os.getenv("OPENAI_API_KEY")
            base_url: Optional[str]
            if self.provider == LLMProvider.OPENAI:
                base_url = self.config.llm_base_url
            else:
                api_key = api_key or "EMPTY"
                base_url = self.config.llm_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

            self.openai_client = OpenAI(api_key=api_key, base_url=base_url)

        elif self.provider == LLMProvider.OLLAMA:
            self.ollama_url = f"{self.config.llm_base_url.rstrip('/')}/api/generate"

        elif self.provider == LLMProvider.GLM:
            self.glm_api_key = self.config.llm_api_key or os.getenv("GLM_API_KEY")

    def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        try:
            if self.provider in (LLMProvider.OPENAI, LLMProvider.QWEN):
                return self._generate_openai(prompt, system_prompt)
            if self.provider == LLMProvider.OLLAMA:
                return self._generate_ollama(prompt, system_prompt)
            if self.provider == LLMProvider.GLM:
                return self._generate_glm(prompt, system_prompt)
        except Exception as exc:
            logger.exception("LLM generation failed")
            raise RuntimeError(f"LLM generate failed: {exc}") from exc
        return None

    def _generate_openai(self, prompt: str, system_prompt: str) -> str:
        completion = self.openai_client.chat.completions.create(
            model=self.config.llm_model,
            messages=[m for m in [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt},
            ] if m],
            temperature=self.config.llm_temperature,
        )
        return completion.choices[0].message.content.strip()

    def _generate_ollama(self, prompt: str, system_prompt: str) -> str:
        payload = {
            "model": self.config.llm_model,
            "prompt": f"{system_prompt}\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "temperature": self.config.llm_temperature,
        }
        resp = requests.post(self.ollama_url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return (data.get("response") or "").strip()

    def _generate_glm(self, prompt: str, system_prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.glm_api_key}",
        }
        data = {
            "model": self.config.llm_model,
            "messages": [m for m in [
                {"role": "system", "content": system_prompt} if system_prompt else None,
                {"role": "user", "content": prompt},
            ] if m],
            "temperature": self.config.llm_temperature,
        }
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        return payload["choices"][0]["message"]["content"].strip()

"""
聊天Agent
基于LangGraph工作流的聊天节点实现。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from app.services import LLMClient


class ChatAgentInput(BaseModel):
    """输入结构，供LangGraph节点或Supervisor调用。"""

    message: str
    context: Dict[str, Any] = Field()


class ChatAgentOutput(BaseModel):
    """聊天Agent的标准输出。"""

    answer: str
    type: str = "chat"
    metadata: Dict[str, Any] = Field()


class ChatAgent(BaseAgent):
    """聊天Agent - 处理闲聊和一般对话。"""

    _TEMPLATES: Dict[str, List[str]] = {
        "greeting": [
            "您好！我是GustoBot，您的智能菜谱助手。有什么菜谱相关的问题吗？",
            "你好！很高兴为您服务。需要推荐菜谱或了解做法吗？",
            "嗨！我可以帮您查找菜谱、了解食材和烹饪技巧哦。"
        ],
        "thanks": [
            "不客气！很高兴能帮到您。还有其他菜谱问题吗？",
            "您太客气了！随时为您服务。",
            "很荣幸能帮到您！有任何菜谱问题都可以问我。"
        ],
        "goodbye": [
            "再见！祝您烹饪愉快！",
            "拜拜！期待下次为您服务。",
            "再见！做出美味菜肴哦！"
        ],
        "default": [
            "我主要专注于帮助您了解菜谱和烹饪知识。有相关问题吗？",
            "作为菜谱助手，我在美食方面可以帮到您。想了解什么菜的做法呢？",
            "我是您的菜谱专家！有什么烹饪问题可以问我。"
        ],
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="ChatAgent",
            description="处理用户的闲聊和一般性对话"
        )
        self.llm_client = llm_client or self._build_llm_client()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理闲聊对话。

        Args:
            input_data: {"message": "...", "context": {...}}
        """
        payload = ChatAgentInput.model_validate(input_data)
        await self.log_action("Processing chat message")

        history = payload.context.get("history")
        if self.llm_client:
            answer = await self._generate_llm_response(payload.message, history)
        else:
            answer = self._generate_template_response(payload.message)

        await self.log_action("Chat response generated")
        return ChatAgentOutput(answer=answer).model_dump()

    def _generate_template_response(self, message: str) -> str:
        """基于模板生成回复。"""
        import random

        message_lower = message.lower()
        if any(word in message_lower for word in ["你好", "您好", "hello", "hi", "嗨"]):
            bucket = "greeting"
        elif any(word in message_lower for word in ["谢谢", "感谢", "thanks", "thank"]):
            bucket = "thanks"
        elif any(word in message_lower for word in ["再见", "拜拜", "bye", "goodbye"]):
            bucket = "goodbye"
        else:
            bucket = "default"

        return random.choice(self._TEMPLATES[bucket])

    async def _generate_llm_response(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]],
    ) -> str:
        """使用LLM生成回复，带上下文。"""
        system_prompt = """你是GustoBot，一个友好的菜谱助手。

当用户进行闲聊时：
1. 保持友好、自然的对话风格
2. 适当引导话题到菜谱和烹饪相关内容
3. 回答要简洁，不要过长
4. 展现你在美食方面的专业性

注意：不要回答与菜谱完全无关的专业问题（如编程、医疗等）。
"""
        try:
            return await self._call_llm(system_prompt, message, history)
        except Exception as exc:
            logger.error(f"LLM chat generation failed: {exc}")
            return self._generate_template_response(message)

    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict[str, Any]]],
    ) -> str:
        """通过LLMClient生成回答。"""
        if not self.llm_client:
            raise RuntimeError("LLM client is not configured.")

        history_messages = self._format_history(history)
        return await self.llm_client.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            context=history_messages,
            temperature=0.6,
        )

    def _format_history(
        self,
        history: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, str]]:
        """转换历史记录为LLM消息格式。"""
        formatted: List[Dict[str, str]] = []
        if not history:
            return formatted

        for item in history[-10:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                formatted.append({"role": role, "content": content})
        return formatted

    @staticmethod
    def _build_llm_client() -> Optional[LLMClient]:
        try:
            return LLMClient()
        except Exception as exc:
            logger.warning(
                "ChatAgent LLM client unavailable, using templates. reason={}",
                exc,
            )
            return None

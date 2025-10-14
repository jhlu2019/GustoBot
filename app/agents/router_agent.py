"""
路由Agent
负责判断用户问题是否与业务相关，并路由到相应的处理Agent。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from app.services import LLMClient


class RouterAgentInput(BaseModel):
    """路由输入结构，用于LangGraph节点。"""

    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class RouterAgentOutput(BaseModel):
    """路由输出结果。"""

    route: str
    reason: str
    confidence: float = 0.0


class RouterAgent(BaseAgent):
    """路由Agent - 判断问题类型并路由。"""

    SYSTEM_PROMPT = """你是一个智能路由系统，负责判断用户问题是否与菜谱、烹饪、食材相关。

分析用户问题，返回以下三种路由之一：
1. "knowledge" - 问题与菜谱、烹饪、食材、营养等相关，需要查询知识库
2. "chat" - 问题是闲聊或一般性问题，但可以友好回应
3. "reject" - 问题完全无关或不适当

返回JSON格式：
{
    "route": "knowledge/chat/reject",
    "reason": "判断原因",
    "confidence": 0.0-1.0
}

确保route字段只包含上述三种取值之一。
"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="RouterAgent",
            description="分析用户问题，判断是否与菜谱相关，并路由到合适的处理Agent"
        )
        self.llm_client = llm_client or self._build_llm_client()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入，判断问题类型。"""
        payload = RouterAgentInput.model_validate(input_data)
        await self.log_action("Routing user question")

        decision = await self._classify_question(payload.message)
        await self.log_action("Routing completed", decision.model_dump())
        return decision.model_dump()

    async def _classify_question(self, message: str) -> RouterAgentOutput:
        """使用LLM或规则进行分类。"""
        if not self.llm_client:
            return RouterAgentOutput(**self._rule_based_classification(message))

        try:
            response = await self._call_llm(self.SYSTEM_PROMPT, message)
            if not response:
                raise ValueError("Empty classification response")

            route = response.get("route", "knowledge")
            if route not in {"knowledge", "chat", "reject"}:
                route = "knowledge"

            reason = response.get("reason", "模型未提供原因")
            confidence = float(response.get("confidence", 0.6))

            return RouterAgentOutput(
                route=route,
                reason=reason,
                confidence=max(0.0, min(confidence, 1.0)),
            )
        except Exception as exc:
            logger.error(f"LLM classification failed: {exc}, falling back to rule-based")
            return RouterAgentOutput(**self._rule_based_classification(message))

    def _rule_based_classification(self, message: str) -> Dict[str, Any]:
        """基于规则的简单分类（作为后备方案）。"""
        message_lower = message.lower()

        recipe_keywords = [
            "菜谱", "食谱", "做法", "怎么做", "烹饪", "烧", "炒", "煮", "蒸", "炖",
            "食材", "配料", "营养", "热量", "卡路里", "健康", "料理", "美食",
            "recipe", "cook", "ingredient", "nutrition"
        ]
        chat_keywords = ["你好", "您好", "谢谢", "再见", "hello", "hi", "thanks", "bye"]

        if any(keyword in message_lower for keyword in recipe_keywords):
            return {
                "route": "knowledge",
                "reason": "问题包含菜谱相关关键词",
                "confidence": 0.8,
            }

        if any(keyword in message_lower for keyword in chat_keywords) or len(message) < 10:
            return {
                "route": "chat",
                "reason": "问题为简单闲聊或问候",
                "confidence": 0.7,
            }

        return {
            "route": "knowledge",
            "reason": "无法明确分类，尝试使用知识库",
            "confidence": 0.5,
        }

    async def _call_llm(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """调用LLM进行分类。"""
        if not self.llm_client:
            raise RuntimeError("LLM client is not configured.")

        return await self.llm_client.chat_json(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.0,
        )

    @staticmethod
    def _build_llm_client() -> Optional[LLMClient]:
        try:
            return LLMClient()
        except Exception as exc:
            logger.warning(
                "RouterAgent LLM client unavailable, using rule-based fallback. reason={}",
                exc,
            )
            return None

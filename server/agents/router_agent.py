"""
路由Agent
负责判断用户问题是否与业务相关，并路由到相应的处理Agent
"""
from typing import Dict, Any
from loguru import logger
from .base_agent import BaseAgent


class RouterAgent(BaseAgent):
    """路由Agent - 判断问题类型并路由"""

    def __init__(self, llm_client=None):
        super().__init__(
            name="RouterAgent",
            description="分析用户问题，判断是否与菜谱相关，并路由到合适的处理Agent"
        )
        self.llm_client = llm_client

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户输入，判断问题类型

        Args:
            input_data: 包含用户消息的字典 {"message": "用户问题", "context": {...}}

        Returns:
            路由决策结果 {"route": "knowledge|chat|reject", "reason": "...", "confidence": 0.0-1.0}
        """
        await self.log_action("Routing user question")

        user_message = input_data.get("message", "")
        context = input_data.get("context", {})

        # 使用LLM判断问题类型
        route_result = await self._classify_question(user_message, context)

        await self.log_action("Routing completed", route_result)

        return route_result

    async def _classify_question(self, message: str, context: Dict) -> Dict[str, Any]:
        """
        使用LLM分类用户问题

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            分类结果
        """
        # 定义系统提示词
        system_prompt = """你是一个智能路由系统，负责判断用户问题是否与菜谱、烹饪、食材相关。

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

示例：
- "怎么做红烧肉？" -> knowledge (高相关度)
- "西红柿有什么营养？" -> knowledge (食材相关)
- "你好" -> chat (友好闲聊)
- "今天天气怎么样？" -> chat (一般闲聊)
- "帮我写代码" -> reject (完全无关)
"""

        # 如果没有配置LLM客户端，使用简单规则
        if not self.llm_client:
            return self._rule_based_classification(message)

        try:
            # 调用LLM进行分类
            response = await self._call_llm(system_prompt, message, context)
            return response
        except Exception as e:
            logger.error(f"LLM classification failed: {e}, falling back to rule-based")
            return self._rule_based_classification(message)

    def _rule_based_classification(self, message: str) -> Dict[str, Any]:
        """
        基于规则的简单分类（作为LLM的后备方案）

        Args:
            message: 用户消息

        Returns:
            分类结果
        """
        message_lower = message.lower()

        # 菜谱相关关键词
        recipe_keywords = [
            "菜谱", "食谱", "做法", "怎么做", "烹饪", "烧", "炒", "煮", "蒸", "炖",
            "食材", "配料", "营养", "热量", "卡路里", "健康", "料理", "美食",
            "recipe", "cook", "ingredient", "nutrition"
        ]

        # 闲聊关键词
        chat_keywords = ["你好", "您好", "谢谢", "再见", "hello", "hi", "thanks", "bye"]

        # 检查是否包含菜谱关键词
        if any(keyword in message_lower for keyword in recipe_keywords):
            return {
                "route": "knowledge",
                "reason": "问题包含菜谱相关关键词",
                "confidence": 0.8
            }

        # 检查是否是简单闲聊
        if any(keyword in message_lower for keyword in chat_keywords) or len(message) < 10:
            return {
                "route": "chat",
                "reason": "问题为简单闲聊或问候",
                "confidence": 0.7
            }

        # 默认尝试使用知识库（宽容策略）
        return {
            "route": "knowledge",
            "reason": "无法明确分类，尝试使用知识库",
            "confidence": 0.5
        }

    async def _call_llm(self, system_prompt: str, user_message: str, context: Dict) -> Dict[str, Any]:
        """
        调用LLM进行分类

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            context: 上下文

        Returns:
            LLM分类结果
        """
        # TODO: 实现实际的LLM调用逻辑
        # 这里需要根据配置的LLM服务（OpenAI/Anthropic等）进行调用
        raise NotImplementedError("LLM integration pending")

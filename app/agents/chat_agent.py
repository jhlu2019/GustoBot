"""
聊天Agent
处理一般性闲聊和友好对话
"""
from typing import Dict, Any
from loguru import logger
from .base_agent import BaseAgent


class ChatAgent(BaseAgent):
    """聊天Agent - 处理闲聊和一般对话"""

    def __init__(self, llm_client=None):
        super().__init__(
            name="ChatAgent",
            description="处理用户的闲聊和一般性对话"
        )
        self.llm_client = llm_client

        # 预设回复模板
        self.templates = {
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
            ]
        }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理闲聊对话

        Args:
            input_data: {"message": "用户消息", "context": {...}}

        Returns:
            {"answer": "回答", "type": "chat"}
        """
        await self.log_action("Processing chat message")

        user_message = input_data.get("message", "")
        context = input_data.get("context", {})

        # 生成回复
        if self.llm_client:
            answer = await self._generate_llm_response(user_message, context)
        else:
            answer = self._generate_template_response(user_message)

        await self.log_action("Chat response generated")

        return {
            "answer": answer,
            "type": "chat"
        }

    def _generate_template_response(self, message: str) -> str:
        """
        基于模板生成回复

        Args:
            message: 用户消息

        Returns:
            回复文本
        """
        import random

        message_lower = message.lower()

        # 判断消息类型
        if any(word in message_lower for word in ["你好", "您好", "hello", "hi", "嗨"]):
            return random.choice(self.templates["greeting"])
        elif any(word in message_lower for word in ["谢谢", "感谢", "thanks", "thank"]):
            return random.choice(self.templates["thanks"])
        elif any(word in message_lower for word in ["再见", "拜拜", "bye", "goodbye"]):
            return random.choice(self.templates["goodbye"])
        else:
            return random.choice(self.templates["default"])

    async def _generate_llm_response(self, message: str, context: Dict) -> str:
        """
        使用LLM生成回复

        Args:
            message: 用户消息
            context: 对话上下文

        Returns:
            LLM生成的回复
        """
        system_prompt = """你是GustoBot，一个友好的菜谱助手。

当用户进行闲聊时：
1. 保持友好、自然的对话风格
2. 适当引导话题到菜谱和烹饪相关内容
3. 回答要简洁，不要过长
4. 展现你在美食方面的专业性

注意：不要回答与菜谱完全无关的专业问题（如编程、医疗等）。
"""

        try:
            # TODO: 调用LLM API
            response = await self._call_llm(system_prompt, message, context)
            return response
        except Exception as e:
            logger.error(f"LLM chat generation failed: {e}")
            return self._generate_template_response(message)

    async def _call_llm(self, system_prompt: str, user_message: str, context: Dict) -> str:
        """
        调用LLM生成回复

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            context: 上下文

        Returns:
            LLM生成的回复
        """
        # TODO: 实现实际的LLM调用逻辑
        raise NotImplementedError("LLM integration pending")

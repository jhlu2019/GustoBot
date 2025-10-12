"""
监督Agent
协调整个Multi-Agent流程，管理Agent之间的通信和状态
"""
from typing import Dict, Any, Optional
from loguru import logger
from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .knowledge_agent import KnowledgeAgent
from .chat_agent import ChatAgent


class SupervisorAgent(BaseAgent):
    """监督Agent - 协调整个Multi-Agent系统"""

    def __init__(
        self,
        router: RouterAgent,
        knowledge: KnowledgeAgent,
        chat: ChatAgent
    ):
        super().__init__(
            name="SupervisorAgent",
            description="协调和监督整个Multi-Agent系统的运行"
        )
        self.router = router
        self.knowledge = knowledge
        self.chat = chat

        self.conversation_history = []

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理用户请求的主流程

        Args:
            input_data: {"message": "用户消息", "session_id": "会话ID", "user_id": "用户ID"}

        Returns:
            {"answer": "回答", "type": "...", "metadata": {...}}
        """
        await self.log_action("Starting request processing")

        user_message = input_data.get("message", "")
        session_id = input_data.get("session_id")

        # 构建处理上下文
        context = {
            "session_id": session_id,
            "user_id": input_data.get("user_id"),
            "history": self._get_recent_history(session_id, limit=5)
        }

        try:
            # 1. 路由阶段：判断问题类型
            route_result = await self.router.process({
                "message": user_message,
                "context": context
            })

            route_type = route_result.get("route")
            confidence = route_result.get("confidence", 0.0)

            await self.log_action(
                f"Routed to: {route_type}",
                {"confidence": confidence}
            )

            # 2. 执行阶段：根据路由结果调用相应Agent
            if route_type == "knowledge":
                result = await self.knowledge.process({
                    "message": user_message,
                    "context": context
                })
            elif route_type == "chat":
                result = await self.chat.process({
                    "message": user_message,
                    "context": context
                })
            else:  # reject
                result = {
                    "answer": "抱歉，这个问题超出了我的能力范围。我主要专注于菜谱和烹饪相关的问题。",
                    "type": "reject"
                }

            # 3. 后处理：添加元数据和记录历史
            final_result = {
                **result,
                "metadata": {
                    "route": route_type,
                    "confidence": confidence,
                    "agent": route_type,
                    "timestamp": self._get_timestamp()
                }
            }

            # 记录对话历史
            self._add_to_history(session_id, user_message, final_result["answer"])

            await self.log_action("Request processing completed")

            return final_result

        except Exception as e:
            logger.error(f"Error in supervisor processing: {e}")
            return {
                "answer": "抱歉，处理您的请求时出现错误。请稍后再试。",
                "type": "error",
                "metadata": {
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                }
            }

    def _get_recent_history(self, session_id: Optional[str], limit: int = 5) -> list:
        """
        获取最近的对话历史

        Args:
            session_id: 会话ID
            limit: 返回的历史记录数量

        Returns:
            历史记录列表
        """
        if not session_id:
            return []

        # TODO: 从数据库或缓存中获取历史记录
        # 这里返回内存中的临时历史
        return [
            h for h in self.conversation_history
            if h.get("session_id") == session_id
        ][-limit:]

    def _add_to_history(self, session_id: Optional[str], user_msg: str, bot_msg: str):
        """
        添加对话到历史记录

        Args:
            session_id: 会话ID
            user_msg: 用户消息
            bot_msg: 机器人回复
        """
        if not session_id:
            return

        self.conversation_history.append({
            "session_id": session_id,
            "user_message": user_msg,
            "bot_message": bot_msg,
            "timestamp": self._get_timestamp()
        })

        # 限制内存中的历史记录数量
        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "supervisor": self.get_info(),
            "agents": {
                "router": self.router.get_info(),
                "knowledge": self.knowledge.get_info(),
                "chat": self.chat.get_info()
            },
            "history_size": len(self.conversation_history)
        }

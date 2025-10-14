"""
监督Agent
协调整个Multi-Agent流程，管理Agent之间的通信和状态
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from redis.exceptions import RedisError
from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .knowledge_agent import KnowledgeAgent
from .chat_agent import ChatAgent
from app.services import RedisSemanticCache, RedisConversationHistory


class SupervisorAgent(BaseAgent):
    """监督Agent - 协调整个Multi-Agent系统"""

    def __init__(
        self,
        router: RouterAgent,
        knowledge: KnowledgeAgent,
        chat: ChatAgent,
        semantic_cache: Optional[RedisSemanticCache] = None,
        history_store: Optional[RedisConversationHistory] = None,
    ):
        super().__init__(
            name="SupervisorAgent",
            description="协调和监督整个Multi-Agent系统的运行"
        )
        self.router = router
        self.knowledge = knowledge
        self.chat = chat
        self.semantic_cache = semantic_cache
        self.history_store = history_store

        self.conversation_history: List[Dict[str, Any]] = []

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
        user_id = input_data.get("user_id")

        # 构建处理上下文
        history = await self._get_recent_history(session_id, limit=5)
        context = {
            "session_id": session_id,
            "user_id": user_id,
            "history": history
        }

        try:
            # 预先检查语义缓存
            cache_scope = self._cache_scope(session_id, user_id)
            cache_history = self._prepare_cache_messages(history)
            cache_messages = cache_history + [{"role": "user", "content": user_message}]
            cached_answer: Optional[str] = None
            if self.semantic_cache:
                try:
                    cached_answer = await self.semantic_cache.lookup(
                        cache_messages,
                        scope=cache_scope
                    )
                except RedisError as exc:
                    logger.warning(
                        "Semantic cache lookup skipped due to Redis error: {}",
                        exc,
                    )
                except Exception as exc:
                    logger.warning(
                        "Semantic cache lookup failed unexpectedly: {}",
                        exc,
                    )

            if cached_answer:
                await self._add_to_history(session_id, user_message, cached_answer)
                return {
                    "answer": cached_answer,
                    "type": "cache",
                    "metadata": {
                        "route": "cache",
                        "confidence": 1.0,
                        "agent": "cache",
                        "timestamp": self._get_timestamp(),
                        "cached": True
                    }
                }

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
            await self._add_to_history(session_id, user_message, final_result["answer"])

            if self.semantic_cache and final_result.get("type") in {"knowledge", "chat"}:
                try:
                    await self.semantic_cache.update(
                        cache_messages,
                        final_result["answer"],
                        scope=cache_scope
                    )
                except RedisError as exc:
                    logger.warning(
                        "Semantic cache update skipped due to Redis error: {}",
                        exc,
                    )
                except Exception as exc:
                    logger.warning(
                        "Semantic cache update failed unexpectedly: {}",
                        exc,
                    )

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

    async def _get_recent_history(self, session_id: Optional[str], limit: int = 5) -> list:
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

        if self.history_store:
            try:
                history_records = await self.history_store.get_recent(
                    session_id,
                    limit=limit * 2
                )
                if history_records:
                    return history_records
            except Exception as exc:
                logger.warning(f"Failed to load history from Redis: {exc}")

        # 内存中的临时历史作为回退
        return [
            h for h in self.conversation_history
            if h.get("session_id") == session_id
        ][-limit * 2:]

    async def _add_to_history(self, session_id: Optional[str], user_msg: str, bot_msg: str):
        """
        添加对话到历史记录

        Args:
            session_id: 会话ID
            user_msg: 用户消息
            bot_msg: 机器人回复
        """
        if not session_id:
            return

        timestamp = self._get_timestamp()

        if self.history_store:
            try:
                await self.history_store.append(
                    session_id,
                    "user",
                    user_msg,
                    metadata={"source": "user"}
                )
                await self.history_store.append(
                    session_id,
                    "assistant",
                    bot_msg,
                    metadata={"source": "assistant"}
                )
            except Exception as exc:
                logger.warning(f"Failed to persist history to Redis: {exc}")

        self._append_local_history(session_id, "user", user_msg, timestamp)
        self._append_local_history(session_id, "assistant", bot_msg, timestamp)

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

    def _append_local_history(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: str
    ) -> None:
        """维护内存中的历史记录以便在Redis不可用时回退。"""
        self.conversation_history.append({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": timestamp
        })

        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]

    @staticmethod
    def _cache_scope(session_id: Optional[str], user_id: Optional[str]) -> Optional[str]:
        """确定语义缓存的命名空间。"""
        return user_id or session_id

    @staticmethod
    def _prepare_cache_messages(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """将历史记录转换为语义缓存需要的消息格式。"""
        cache_messages: List[Dict[str, str]] = []
        for record in history:
            if "user_message" in record and "bot_message" in record:
                cache_messages.append({"role": "user", "content": record["user_message"]})
                cache_messages.append({"role": "assistant", "content": record["bot_message"]})
                continue

            role = record.get("role")
            content = record.get("content")
            if role in {"user", "assistant"} and content:
                cache_messages.append({"role": role, "content": content})
        return cache_messages

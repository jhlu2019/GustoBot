"""
监督Agent
使用LangGraph协调路由、知识库和闲聊Agent。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger
from redis.exceptions import RedisError
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

from .base_agent import BaseAgent
from .chat_agent import ChatAgent
from .knowledge_agent import KnowledgeAgent
from .router_agent import RouterAgent
from .state_models import ConversationInput, ConversationState, AgentAnswer, RouterResult
from app.services import RedisConversationHistory, RedisSemanticCache


class SupervisorAgent(BaseAgent):
    """监督Agent - 基于LangGraph协调整个Multi-Agent系统。"""

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

        self.conversation_history: list[dict[str, Any]] = []
        self.workflow = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(dict)

        async def prepare_context(state: dict) -> dict:
            conv = ConversationState.model_validate(state)
            history = await self._get_recent_history(conv.session_id, limit=5)
            conv.history = history
            conv.cache_scope = self._cache_scope(conv.session_id, conv.user_id)
            cache_messages = self._prepare_cache_messages(history)
            cache_messages.append({"role": "user", "content": conv.message})
            conv.cache_messages = cache_messages
            return conv.to_dict()

        async def check_cache(state: dict) -> dict:
            conv = ConversationState.model_validate(state)
            if not self.semantic_cache or not conv.cache_messages:
                return conv.to_dict()

            cached_answer: Optional[str] = None
            try:
                cached_answer = await self.semantic_cache.lookup(
                    conv.cache_messages,
                    scope=conv.cache_scope,
                )
            except RedisError as exc:
                logger.warning("Semantic cache lookup skipped due to Redis error: {}", exc)
            except Exception as exc:
                logger.warning("Semantic cache lookup failed unexpectedly: {}", exc)

            if cached_answer:
                conv.answer = cached_answer
                conv.answer_type = "cache"
                conv.cached = True
                conv.metadata = {
                    "route": "cache",
                    "confidence": 1.0,
                    "agent": "cache",
                    "timestamp": self._get_timestamp(),
                    "cached": True,
                }
            return conv.to_dict()

        async def route_node(state: dict) -> dict:
            conv = ConversationState.model_validate(state)
            route_result = await self.router.process(
                {
                    "message": conv.message,
                    "context": {"history": conv.history},
                }
            )
            decision = RouterResult.model_validate(route_result)
            conv.route = decision.route
            conv.confidence = decision.confidence
            conv.reason = decision.reason
            return conv.to_dict()

        async def knowledge_node(state: dict) -> dict:
            conv = ConversationState.model_validate(state)
            result = await self.knowledge.process(
                {
                    "message": conv.message,
                    "context": {"history": conv.history},
                }
            )
            answer = AgentAnswer(
                answer=result.get("answer", ""),
                type=result.get("type", "knowledge"),
                metadata=result.get("metadata", {}),
            )
            conv.answer = answer.answer
            conv.answer_type = answer.type
            conv.metadata = {
                **answer.metadata,
                "sources": result.get("sources", []),
                "knowledge_confidence": result.get("confidence"),
            }
            # 如果知识节点提供了更可靠的置信度，则覆盖
            if "confidence" in result:
                try:
                    conv.confidence = float(result["confidence"])
                except (TypeError, ValueError):
                    pass
            return conv.to_dict()

        async def chat_node(state: dict) -> dict:
            conv = ConversationState.model_validate(state)
            result = await self.chat.process(
                {
                    "message": conv.message,
                    "context": {"history": conv.history},
                }
            )
            answer = AgentAnswer.model_validate(result)
            conv.answer = answer.answer
            conv.answer_type = answer.type
            conv.metadata = answer.metadata
            return conv.to_dict()

        async def finalize_node(state: dict) -> dict:
            conv = ConversationState.model_validate(state)

            answer = conv.answer
            answer_type = conv.answer_type or conv.route or "unknown"

            if not answer:
                if conv.route == "reject":
                    answer = "抱歉，这个问题超出了我的能力范围。我主要专注于菜谱和烹饪相关的问题。"
                    answer_type = "reject"
                else:
                    answer = "抱歉，处理您的请求时出现错误。请稍后再试。"
                    answer_type = "error"

            metadata = {**(conv.metadata or {})}
            metadata.setdefault("route", conv.route or answer_type)
            metadata.setdefault("confidence", conv.confidence)
            metadata.setdefault("agent", conv.route or answer_type)
            metadata.setdefault("timestamp", self._get_timestamp())
            metadata.setdefault("cached", conv.cached)
            if conv.reason:
                metadata.setdefault("reason", conv.reason)

            conv.answer = answer
            conv.answer_type = answer_type
            conv.metadata = metadata

            if conv.session_id:
                await self._add_to_history(conv.session_id, conv.message, conv.answer)
                if (
                    self.semantic_cache
                    and not conv.cached
                    and conv.answer_type in {"knowledge", "chat"}
                    and conv.cache_messages
                ):
                    try:
                        await self.semantic_cache.update(
                            conv.cache_messages,
                            conv.answer,
                            scope=conv.cache_scope,
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

            return conv.to_dict()

        def cache_branch(state: dict) -> str:
            conv = ConversationState.model_validate(state)
            return "cached" if conv.cached else "miss"

        def route_branch(state: dict) -> str:
            conv = ConversationState.model_validate(state)
            if conv.route == "knowledge":
                return "knowledge"
            if conv.route == "chat":
                return "chat"
            return "reject"

        graph.add_node("prepare_context", prepare_context)
        graph.add_node("check_cache", check_cache)
        graph.add_node("route", route_node)
        graph.add_node("knowledge", knowledge_node)
        graph.add_node("chat", chat_node)
        graph.add_node("finalize", finalize_node)

        graph.add_edge(START, "prepare_context")
        graph.add_edge("prepare_context", "check_cache")
        graph.add_conditional_edges(
            "check_cache",
            cache_branch,
            {"cached": "finalize", "miss": "route"},
        )
        graph.add_conditional_edges(
            "route",
            route_branch,
            {"knowledge": "knowledge", "chat": "chat", "reject": "finalize"},
        )
        graph.add_edge("knowledge", "finalize")
        graph.add_edge("chat", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """入口：执行LangGraph工作流。"""
        try:
            convo_input = ConversationInput.model_validate(input_data)
        except ValidationError as exc:
            logger.error(f"Invalid supervisor input: {exc}")
            raise

        state = ConversationState(
            message=convo_input.message,
            session_id=convo_input.session_id,
            user_id=convo_input.user_id,
        )

        result_state = await self.workflow.ainvoke(state.to_dict())
        final_state = ConversationState.model_validate(result_state)

        return {
            "answer": final_state.answer,
            "type": final_state.answer_type or "unknown",
            "metadata": final_state.metadata,
        }

    async def _get_recent_history(self, session_id: Optional[str], limit: int = 5) -> list:
        """获取最近的对话历史。"""
        if not session_id:
            return []

        if self.history_store:
            try:
                history_records = await self.history_store.get_recent(
                    session_id,
                    limit=limit * 2,
                )
                if history_records:
                    return history_records
            except Exception as exc:
                logger.warning(f"Failed to load history from Redis: {exc}")

        return [
            h for h in self.conversation_history
            if h.get("session_id") == session_id
        ][-limit * 2:]

    async def _add_to_history(self, session_id: Optional[str], user_msg: str, bot_msg: str):
        """添加对话到历史记录。"""
        if not session_id:
            return

        timestamp = self._get_timestamp()

        if self.history_store:
            try:
                await self.history_store.append(
                    session_id,
                    "user",
                    user_msg,
                    metadata={"source": "user"},
                )
                await self.history_store.append(
                    session_id,
                    "assistant",
                    bot_msg,
                    metadata={"source": "assistant"},
                )
            except Exception as exc:
                logger.warning(f"Failed to persist history to Redis: {exc}")

        self._append_local_history(session_id, "user", user_msg, timestamp)
        self._append_local_history(session_id, "assistant", bot_msg, timestamp)

    def _append_local_history(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: str,
    ) -> None:
        """维护内存中的历史记录以便在Redis不可用时回退。"""
        self.conversation_history.append({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        })

        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]

    @staticmethod
    def _cache_scope(session_id: Optional[str], user_id: Optional[str]) -> Optional[str]:
        """确定语义缓存的命名空间。"""
        return user_id or session_id

    @staticmethod
    def _prepare_cache_messages(history: list[Dict[str, Any]]) -> list[Dict[str, str]]:
        """将历史记录转换为语义缓存需要的消息格式。"""
        cache_messages: list[Dict[str, str]] = []
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

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳。"""
        from datetime import datetime

        return datetime.now().isoformat()

"""
Refactored SupervisorAgent using pure function nodes and TypedDict state.
Uses modern LangGraph patterns for better maintainability and type safety.
"""
from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import Any, Dict, Literal, Optional

from loguru import logger
from redis.exceptions import RedisError
from langgraph.graph import StateGraph, START, END

from .state_models import ConversationInput, ConversationState
from .nodes import route_question, answer_from_knowledge, chat_response
from app.services import LLMClient, RedisConversationHistory, RedisSemanticCache


class SupervisorAgent:
    """
    Supervisor agent that orchestrates the multi-agent workflow using LangGraph.
    Refactored to use pure function nodes and TypedDict state.
    """

    def __init__(
        self,
        knowledge_service: Any,
        llm_client: Optional[LLMClient] = None,
        semantic_cache: Optional[RedisSemanticCache] = None,
        history_store: Optional[RedisConversationHistory] = None,
    ):
        """
        Initialize supervisor with dependencies.

        Args:
            knowledge_service: Service for knowledge base queries
            llm_client: LLM client for all agents (shared)
            semantic_cache: Optional semantic cache for responses
            history_store: Optional Redis-based conversation history
        """
        self.knowledge_service = knowledge_service
        self.llm_client = llm_client
        self.semantic_cache = semantic_cache
        self.history_store = history_store

        # In-memory fallback for conversation history
        self.conversation_history: list[dict[str, Any]] = []

        # Build the workflow graph
        self.workflow = self._build_graph()

        logger.info("SupervisorAgent initialized with pure function nodes")

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow with pure function nodes."""
        graph = StateGraph(ConversationState)

        # ====================================================================
        # Node: Prepare Context
        # ====================================================================
        async def prepare_context(state: ConversationState) -> ConversationState:
            """Load conversation history and prepare cache context."""
            session_id = state.get("session_id")
            user_id = state.get("user_id")

            history = await self._get_recent_history(session_id, limit=5)
            cache_scope = self._cache_scope(session_id, user_id)
            cache_messages = self._prepare_cache_messages(history)
            cache_messages.append({"role": "user", "content": state["message"]})

            return {
                **state,
                "history": history,
                "cache_scope": cache_scope,
                "cache_messages": cache_messages,
            }

        # ====================================================================
        # Node: Check Cache
        # ====================================================================
        async def check_cache(state: ConversationState) -> ConversationState:
            """Check semantic cache for existing answer."""
            if not self.semantic_cache or not state.get("cache_messages"):
                return state

            cached_answer: Optional[str] = None
            try:
                cached_answer = await self.semantic_cache.lookup(
                    state["cache_messages"],
                    scope=state.get("cache_scope"),
                )
            except RedisError as exc:
                logger.warning(f"Semantic cache lookup skipped due to Redis error: {exc}")
            except Exception as exc:
                logger.warning(f"Semantic cache lookup failed unexpectedly: {exc}")

            if cached_answer:
                logger.info("[CacheNode] Cache hit!")
                return {
                    **state,
                    "answer": cached_answer,
                    "answer_type": "cache",
                    "cached": True,
                    "metadata": {
                        "route": "cache",
                        "confidence": 1.0,
                        "agent": "cache",
                        "timestamp": self._get_timestamp(),
                        "cached": True,
                    },
                }

            return {**state, "cached": False}

        # ====================================================================
        # Node: Finalize
        # ====================================================================
        async def finalize(state: ConversationState) -> ConversationState:
            """Finalize response, persist history, and update cache."""
            answer = state.get("answer")
            answer_type = state.get("answer_type") or state.get("route") or "unknown"

            # Provide default answer if missing
            if not answer:
                route = state.get("route")
                if route == "reject":
                    answer = "抱歉，这个问题超出了我的能力范围。我主要专注于菜谱和烹饪相关的问题。"
                    answer_type = "reject"
                else:
                    answer = "抱歉，处理您的请求时出现错误。请稍后再试。"
                    answer_type = "error"

            # Build metadata
            metadata = state.get("metadata", {}).copy()
            metadata.setdefault("route", state.get("route") or answer_type)
            metadata.setdefault("confidence", state.get("confidence", 0.0))
            metadata.setdefault("agent", state.get("route") or answer_type)
            metadata.setdefault("timestamp", self._get_timestamp())
            metadata.setdefault("cached", state.get("cached", False))
            if state.get("reason"):
                metadata.setdefault("reason", state["reason"])

            # Persist to history
            session_id = state.get("session_id")
            if session_id:
                await self._add_to_history(session_id, state["message"], answer)

                # Update semantic cache
                if (
                    self.semantic_cache
                    and not state.get("cached")
                    and answer_type in {"knowledge", "chat"}
                    and state.get("cache_messages")
                ):
                    try:
                        await self.semantic_cache.update(
                            state["cache_messages"],
                            answer,
                            scope=state.get("cache_scope"),
                        )
                    except RedisError as exc:
                        logger.warning(f"Semantic cache update skipped due to Redis error: {exc}")
                    except Exception as exc:
                        logger.warning(f"Semantic cache update failed unexpectedly: {exc}")

            return {
                **state,
                "answer": answer,
                "answer_type": answer_type,
                "metadata": metadata,
            }

        # ====================================================================
        # Routing Conditions
        # ====================================================================
        def cache_branch(state: ConversationState) -> Literal["cached", "miss"]:
            """Determine if cache hit or miss."""
            return "cached" if state.get("cached") else "miss"

        def route_branch(state: ConversationState) -> Literal["knowledge", "chat", "reject"]:
            """Determine which agent to use based on route."""
            route = state.get("route", "knowledge")
            if route in {"knowledge", "chat", "reject"}:
                return route
            return "knowledge"  # Default fallback

        # ====================================================================
        # Add Nodes
        # ====================================================================
        graph.add_node("prepare_context", prepare_context)
        graph.add_node("check_cache", check_cache)

        # Use partial to bind dependencies to pure functions
        graph.add_node(
            "route",
            partial(route_question, llm_client=self.llm_client)
        )
        graph.add_node(
            "knowledge",
            partial(
                answer_from_knowledge,
                knowledge_service=self.knowledge_service,
                llm_client=self.llm_client,
            )
        )
        graph.add_node(
            "chat",
            partial(chat_response, llm_client=self.llm_client)
        )
        graph.add_node("finalize", finalize)

        # ====================================================================
        # Add Edges
        # ====================================================================
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
        """
        Process user input through the workflow.

        Args:
            input_data: {"message": str, "session_id": str, "user_id": str}

        Returns:
            {"answer": str, "type": str, "metadata": dict}
        """
        convo_input = ConversationInput.model_validate(input_data)

        initial_state: ConversationState = {
            "message": convo_input.message,
            "session_id": convo_input.session_id,
            "user_id": convo_input.user_id,
        }

        logger.info(f"[Supervisor] Processing message: {convo_input.message[:50]}...")

        result_state = await self.workflow.ainvoke(initial_state)

        return {
            "answer": result_state.get("answer", ""),
            "type": result_state.get("answer_type", "unknown"),
            "metadata": result_state.get("metadata", {}),
        }

    async def stream(self, input_data: Dict[str, Any]):
        """
        Stream workflow execution events.

        Args:
            input_data: {"message": str, "session_id": str, "user_id": str}

        Yields:
            State updates as the workflow progresses
        """
        convo_input = ConversationInput.model_validate(input_data)

        initial_state: ConversationState = {
            "message": convo_input.message,
            "session_id": convo_input.session_id,
            "user_id": convo_input.user_id,
        }

        logger.info(f"[Supervisor] Streaming message: {convo_input.message[:50]}...")

        async for event in self.workflow.astream(initial_state):
            yield event

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_recent_history(
        self,
        session_id: Optional[str],
        limit: int = 5
    ) -> list[Dict[str, Any]]:
        """Get recent conversation history."""
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

        # Fallback to in-memory history
        return [
            h for h in self.conversation_history
            if h.get("session_id") == session_id
        ][-limit * 2:]

    async def _add_to_history(
        self,
        session_id: Optional[str],
        user_msg: str,
        bot_msg: str
    ):
        """Add conversation to history."""
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

        # Maintain in-memory history
        self._append_local_history(session_id, "user", user_msg, timestamp)
        self._append_local_history(session_id, "assistant", bot_msg, timestamp)

    def _append_local_history(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: str,
    ) -> None:
        """Append to in-memory history with rotation."""
        self.conversation_history.append({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        })

        # Rotate history to prevent unbounded growth
        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]

    @staticmethod
    def _cache_scope(session_id: Optional[str], user_id: Optional[str]) -> Optional[str]:
        """Determine cache scope (namespace)."""
        return user_id or session_id

    @staticmethod
    def _prepare_cache_messages(history: list[Dict[str, Any]]) -> list[Dict[str, str]]:
        """Convert history to cache message format."""
        cache_messages: list[Dict[str, str]] = []
        for record in history:
            # Handle both formats
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
        """Get current ISO timestamp."""
        return datetime.now().isoformat()

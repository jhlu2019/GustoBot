"""
LangGraph node functions for the GustoBot workflow.
Each function is a pure function that takes state and returns updated state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from .state_models import ConversationState
from app.services import LLMClient, RedisConversationHistory, RedisSemanticCache


# ============================================================================
# Router Node Functions
# ============================================================================

ROUTER_SYSTEM_PROMPT = """你是一个智能路由系统，负责判断用户问题是否与菜谱、烹饪、食材相关。

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


async def route_question(
    state: ConversationState,
    llm_client: Optional[LLMClient] = None,
) -> ConversationState:
    """
    Route user question to appropriate handler.

    Args:
        state: Current conversation state
        llm_client: LLM client for classification (optional)

    Returns:
        Updated state with route, confidence, and reason
    """
    message = state["message"]
    logger.info(f"[RouterNode] Routing question: {message[:50]}...")

    if not llm_client:
        decision = _rule_based_classification(message)
    else:
        try:
            response = await llm_client.chat_json(
                system_prompt=ROUTER_SYSTEM_PROMPT,
                user_message=message,
                temperature=0.0,
            )

            route = response.get("route", "knowledge")
            if route not in {"knowledge", "chat", "reject"}:
                route = "knowledge"

            decision = {
                "route": route,
                "reason": response.get("reason", "模型未提供原因"),
                "confidence": max(0.0, min(float(response.get("confidence", 0.6)), 1.0)),
            }
        except Exception as exc:
            logger.error(f"LLM classification failed: {exc}, falling back to rules")
            decision = _rule_based_classification(message)

    logger.info(f"[RouterNode] Decision: {decision['route']} (confidence: {decision['confidence']})")

    return {
        **state,
        "route": decision["route"],
        "confidence": decision["confidence"],
        "reason": decision["reason"],
    }


def _rule_based_classification(message: str) -> Dict[str, Any]:
    """Rule-based fallback classification."""
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


# ============================================================================
# Knowledge Node Functions
# ============================================================================

KNOWLEDGE_SYSTEM_PROMPT = """你是一个专业的菜谱助手，基于提供的知识库内容回答用户问题。

要求：
1. 只基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 回答要准确、详细、实用
4. 如果是烹饪步骤，要按顺序清晰列出
5. 回答要友好、自然

参考文档：
{context}

请基于以上文档回答用户问题。
"""


async def answer_from_knowledge(
    state: ConversationState,
    knowledge_service: Any,
    llm_client: Optional[LLMClient] = None,
) -> ConversationState:
    """
    Answer question using knowledge base (RAG).

    Args:
        state: Current conversation state
        knowledge_service: Knowledge base service for retrieval
        llm_client: LLM client for answer generation

    Returns:
        Updated state with answer, sources, and metadata
    """
    message = state["message"]
    logger.info(f"[KnowledgeNode] Processing with knowledge base: {message[:50]}...")

    # Retrieve relevant documents
    try:
        docs = await knowledge_service.search(message)
        logger.info(f"[KnowledgeNode] Retrieved {len(docs)} documents")
    except Exception as exc:
        logger.error(f"Document retrieval failed: {exc}")
        docs = []

    if not docs:
        return {
            **state,
            "answer": "抱歉，我在知识库中没有找到相关信息。您可以换个方式提问吗？",
            "answer_type": "knowledge",
            "metadata": {
                **state.get("metadata", {}),
                "sources": [],
                "reason": "no_documents",
            },
        }

    # Prepare context from documents
    context_text = "\n\n".join(
        f"文档 {idx + 1}:\n{doc.get('content', '')}"
        for idx, doc in enumerate(docs[:5])
    )

    sources = [doc.get("source", "") for doc in docs]
    confidence = _calculate_confidence(docs)

    # Generate answer using LLM
    if not llm_client:
        answer = docs[0].get("content", "找到相关内容，但无法生成回答")
        metadata = {"reason": "llm_missing"}
    else:
        try:
            answer = await llm_client.chat(
                system_prompt=KNOWLEDGE_SYSTEM_PROMPT.format(context=context_text),
                user_message=message,
                temperature=0.3,
            )
            metadata = {}
        except Exception as exc:
            logger.error(f"Answer generation failed: {exc}")
            answer = "抱歉，生成回答时出现错误。"
            metadata = {"reason": "llm_failure", "error": str(exc)}

    logger.info(f"[KnowledgeNode] Answer generated (confidence: {confidence})")

    return {
        **state,
        "answer": answer,
        "answer_type": "knowledge",
        "confidence": confidence,
        "metadata": {
            **state.get("metadata", {}),
            **metadata,
            "sources": sources,
            "knowledge_confidence": confidence,
        },
    }


def _calculate_confidence(documents: List[Dict[str, Any]]) -> float:
    """Calculate confidence based on document similarity scores."""
    if not documents:
        return 0.0
    avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
    return min(max(avg_score, 0.0), 1.0)


# ============================================================================
# Chat Node Functions
# ============================================================================

CHAT_SYSTEM_PROMPT = """你是GustoBot，一个友好的菜谱助手。

当用户进行闲聊时：
1. 保持友好、自然的对话风格
2. 适当引导话题到菜谱和烹饪相关内容
3. 回答要简洁，不要过长
4. 展现你在美食方面的专业性

注意：不要回答与菜谱完全无关的专业问题（如编程、医疗等）。
"""

CHAT_TEMPLATES: Dict[str, List[str]] = {
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


async def chat_response(
    state: ConversationState,
    llm_client: Optional[LLMClient] = None,
) -> ConversationState:
    """
    Generate friendly chat response.

    Args:
        state: Current conversation state
        llm_client: LLM client for response generation (optional)

    Returns:
        Updated state with chat answer
    """
    message = state["message"]
    history = state.get("history", [])

    logger.info(f"[ChatNode] Generating chat response for: {message[:50]}...")

    if llm_client:
        try:
            history_messages = _format_history(history)
            answer = await llm_client.chat(
                system_prompt=CHAT_SYSTEM_PROMPT,
                user_message=message,
                context=history_messages,
                temperature=0.6,
            )
        except Exception as exc:
            logger.error(f"LLM chat generation failed: {exc}")
            answer = _generate_template_response(message)
    else:
        answer = _generate_template_response(message)

    logger.info(f"[ChatNode] Chat response generated")

    return {
        **state,
        "answer": answer,
        "answer_type": "chat",
    }


def _generate_template_response(message: str) -> str:
    """Generate template-based response."""
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

    return random.choice(CHAT_TEMPLATES[bucket])


def _format_history(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """Format conversation history for LLM."""
    formatted: List[Dict[str, str]] = []
    if not history:
        return formatted

    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            formatted.append({"role": role, "content": content})
    return formatted

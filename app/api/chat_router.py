"""
聊天API端点
Chat API Endpoints with streaming support
"""
from __future__ import annotations
import json
import uuid
from typing import Any, Dict, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from redis.asyncio import Redis

from ..config import settings
from ..models.chat import ChatRequest, ChatResponse
from ..services import RedisConversationHistory, RedisSemanticCache, LLMClient


router = APIRouter(prefix="/chat", tags=["chat"])

_redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
_semantic_cache = RedisSemanticCache(redis_client=_redis_client, prefix="conversation")
_history_store = RedisConversationHistory(redis_client=_redis_client, prefix="conversation")


# 依赖注入：获取supervisor agent (新版本)
def get_supervisor():
    """获取重构后的 Supervisor Agent 实例"""
    from ..agents.supervisor_agent_v2 import SupervisorAgent
    from ..knowledge_base import KnowledgeService

    # 初始化服务
    knowledge_service = KnowledgeService()
    llm_client = LLMClient()

    supervisor = SupervisorAgent(
        knowledge_service=knowledge_service,
        llm_client=llm_client,
        semantic_cache=_semantic_cache,
        history_store=_history_store,
    )

    return supervisor


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    supervisor: SupervisorAgent = Depends(get_supervisor)
) -> ChatResponse:
    """
    处理用户聊天消息

    - **message**: 用户消息内容
    - **session_id**: 可选的会话ID，用于维护对话上下文
    - **user_id**: 可选的用户ID
    """
    try:
        # 生成session_id（如果未提供）
        session_id = request.session_id or str(uuid.uuid4())

        # 构建输入
        input_data = {
            "message": request.message,
            "session_id": session_id,
            "user_id": request.user_id
        }

        # 处理请求
        result = await supervisor.process(input_data)

        # 构建响应
        response = ChatResponse(
            answer=result.get("answer", "抱歉，无法生成回答"),
            session_id=session_id,
            type=result.get("type", "unknown"),
            metadata=result.get("metadata", {})
        )

        logger.info(f"Chat processed: session={session_id}, type={response.type}")

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"处理消息时出错: {str(e)}")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    supervisor = Depends(get_supervisor)
):
    """
    流式处理用户聊天消息

    - **message**: 用户消息内容
    - **session_id**: 可选的会话ID
    - **user_id**: 可选的用户ID

    返回 Server-Sent Events (SSE) 流
    """
    async def event_generator() -> AsyncIterator[str]:
        try:
            # 生成session_id（如果未提供）
            session_id = request.session_id or str(uuid.uuid4())

            # 构建输入
            input_data = {
                "message": request.message,
                "session_id": session_id,
                "user_id": request.user_id
            }

            # 流式处理
            async for event in supervisor.stream(input_data):
                # 发送每个节点的状态更新
                event_data = {
                    "session_id": session_id,
                    "event": event,
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = {
                "error": str(e),
                "session_id": session_id if 'session_id' in locals() else None
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    获取系统状态

    返回系统健康状态
    """
    try:
        return {
            "status": "ok",
            "message": "GustoBot Multi-Agent System (LangGraph v2)",
            "version": "2.0.0",
            "features": [
                "TypedDict state management",
                "Pure function nodes",
                "Streaming support",
                "Semantic caching",
                "Conversation history"
            ]
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

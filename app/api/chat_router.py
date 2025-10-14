"""
聊天API端点
Chat API Endpoints
"""
from __future__ import annotations
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from redis.asyncio import Redis

from ..agents import SupervisorAgent
from ..config import settings
from ..models.chat import ChatRequest, ChatResponse
from ..services import RedisConversationHistory, RedisSemanticCache


router = APIRouter(prefix="/chat", tags=["chat"])

_redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)
_semantic_cache = RedisSemanticCache(redis_client=_redis_client, prefix="conversation")
_history_store = RedisConversationHistory(redis_client=_redis_client, prefix="conversation")


# 依赖注入：获取supervisor agent
def get_supervisor():
    """获取Supervisor Agent实例"""
    from ..agents import SupervisorAgent, RouterAgent, KnowledgeAgent, ChatAgent
    from ..knowledge_base import KnowledgeService

    # 初始化服务和agents
    knowledge_service = KnowledgeService()

    router_agent = RouterAgent()
    knowledge_agent = KnowledgeAgent(knowledge_service=knowledge_service)
    chat_agent = ChatAgent()

    supervisor = SupervisorAgent(
        router=router_agent,
        knowledge=knowledge_agent,
        chat=chat_agent,
        semantic_cache=_semantic_cache,
        history_store=_history_store
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


@router.get("/status")
async def get_status(supervisor: SupervisorAgent = Depends(get_supervisor)) -> Dict[str, Any]:
    """
    获取系统状态

    返回各个Agent的状态信息
    """
    try:
        status = await supervisor.get_system_status()
        return {
            "status": "ok",
            "data": status
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

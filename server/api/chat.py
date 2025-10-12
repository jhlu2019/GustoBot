"""
聊天API端点
Chat API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])


# 请求模型
class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "怎么做红烧肉？",
                "session_id": "session_123",
                "user_id": "user_456"
            }
        }


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str = Field(..., description="回答")
    session_id: str = Field(..., description="会话ID")
    type: str = Field(..., description="响应类型：knowledge/chat/reject/error")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "红烧肉的做法是...",
                "session_id": "session_123",
                "type": "knowledge",
                "metadata": {
                    "route": "knowledge",
                    "confidence": 0.95
                }
            }
        }


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
        chat=chat_agent
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

"""
Unified Chat API with Agent Integration

Provides a single endpoint for chat interactions with automatic routing.
"""
import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from gustobot.application.agents.lg_builder import graph
from gustobot.config import settings
from gustobot.infrastructure.core.database import get_db
from gustobot.infrastructure.persistence.crud import chat_message, chat_session
from gustobot.interfaces.http.models.chat_message import ChatMessageCreate, ChatMessageResponse
from gustobot.interfaces.http.models.chat_session import ChatSessionCreate, ChatSessionResponse
from sqlalchemy.orm import Session

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field("default_user", description="User identifier")
    stream: bool = Field(False, description="Enable streaming response")
    image_path: Optional[str] = Field(None, description="Path to uploaded image file")
    file_path: Optional[str] = Field(None, description="Path to uploaded file")


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    session_id: str
    message_id: str
    route: Optional[str] = None
    route_logic: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatStreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str = Field(..., description="Chunk type: 'message', 'metadata', 'error', 'done'")
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    route: Optional[str] = None


def get_or_create_session(db: Session, session_id: Optional[str], user_id: str) -> str:
    """Get existing session or create new one"""
    if session_id:
        session = chat_session.get(db, id=session_id)
        if session:
            return session_id

    # Create new session
    new_session_id = str(uuid.uuid4())
    session_data = ChatSessionCreate(
        id=new_session_id,
        user_id=user_id,
        title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    chat_session.create(db, obj_in=session_data)
    return new_session_id


async def save_message(db: Session, session_id: str, message: str, is_user: bool,
                       route: Optional[str] = None, metadata: Optional[Dict] = None):
    """Save message to database"""
    try:
        message_data = ChatMessageCreate(
            session_id=session_id,
            message=message,
            is_user=is_user,
            route=route,
            metadata=metadata or {}
        )
        chat_message.create(db, obj_in=message_data)
    except Exception as e:
        logger.error(f"Failed to save message: {e}")


async def process_agent_query(message: str, session_id: str,
                            image_path: Optional[str] = None,
                            file_path: Optional[str] = None) -> Dict[str, Any]:
    """Process query through agent system"""
    config = {
        "configurable": {
            "thread_id": session_id,
            "image_path": image_path,
            "file_path": file_path,
        }
    }

    input_state = {
        "messages": [{"type": "human", "content": message}]
    }

    try:
        # Invoke agent graph
        result = await graph.ainvoke(input_state, config=config)

        # Extract response and metadata
        response_text = ""
        if result.get("messages"):
            response_text = result["messages"][-1].content

        # Extract route information
        router_info = result.get("router", {})
        route = router_info.get("type")
        route_logic = router_info.get("logic")

        # Extract sources if available
        sources = result.get("sources", [])

        return {
            "message": response_text,
            "route": route,
            "route_logic": route_logic,
            "sources": sources,
            "metadata": {
                "session_id": session_id,
                "agent_state": result
            }
        }
    except Exception as e:
        logger.error(f"Agent query failed: {e}", exc_info=True)
        return {
            "message": "抱歉，处理您的请求时出现了错误。请稍后重试。",
            "route": "error",
            "route_logic": f"Error: {str(e)}",
            "sources": [],
            "metadata": {"error": str(e)}
        }


async def stream_agent_response(message: str, session_id: str,
                               image_path: Optional[str] = None,
                               file_path: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Stream agent response"""
    # Send initial metadata
    metadata_chunk = ChatStreamChunk(
        type="metadata",
        metadata={"status": "processing"},
        session_id=session_id
    )
    yield f"data: {metadata_chunk.model_dump_json()}\n\n"

    try:
        # Process the query
        result = await process_agent_query(message, session_id, image_path, file_path)

        # Send route information
        route_chunk = ChatStreamChunk(
            type="metadata",
            metadata={"route": result["route"], "logic": result["route_logic"]},
            session_id=session_id,
            route=result["route"]
        )
        yield f"data: {route_chunk.model_dump_json()}\n\n"

        # Stream the response message (simulated - in real implementation, you'd stream from LLM)
        response_text = result["message"]
        words = response_text.split()
        current_text = ""

        for word in words:
            current_text += word + " "
            message_chunk = ChatStreamChunk(
                type="message",
                content=word + " ",
                session_id=session_id
            )
            yield f"data: {message_chunk.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)  # Simulate streaming delay

        # Send done signal
        done_chunk = ChatStreamChunk(
            type="done",
            metadata={"sources": result.get("sources", [])},
            session_id=session_id
        )
        yield f"data: {done_chunk.model_dump_json()}\n\n"

    except Exception as e:
        # Send error
        error_chunk = ChatStreamChunk(
            type="error",
            content=f"处理请求时出错: {str(e)}",
            session_id=session_id
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Unified chat endpoint with automatic agent routing

    - Automatically routes queries to appropriate agents
    - Maintains conversation history
    - Supports file uploads and images
    """
    # Get or create session
    session_id = get_or_create_session(db, request.session_id, request.user_id)

    # Save user message
    await save_message(db, session_id, request.message, is_user=True)

    # Process through agent
    result = await process_agent_query(
        request.message,
        session_id,
        request.image_path,
        request.file_path
    )

    # Save assistant message
    message_id = await save_message(
        db,
        session_id,
        result["message"],
        is_user=False,
        route=result["route"],
        metadata=result.get("metadata")
    )

    return ChatResponse(
        message=result["message"],
        session_id=session_id,
        message_id=message_id or str(uuid.uuid4()),
        route=result["route"],
        route_logic=result["route_logic"],
        sources=result.get("sources"),
        metadata=result.get("metadata")
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Streaming chat endpoint with automatic agent routing

    Returns responses in Server-Sent Events (SSE) format
    """
    # Get or create session
    session_id = get_or_create_session(db, request.session_id, request.user_id)

    # Save user message
    await save_message(db, session_id, request.message, is_user=True)

    # Save assistant message in background
    async def save_assistant_message(response_text: str):
        await save_message(db, session_id, response_text, is_user=False)

    # Return streaming response
    return StreamingResponse(
        stream_agent_response(request.message, session_id, request.image_path, request.file_path),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/chat/history/{session_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
) -> List[ChatMessageResponse]:
    """
    Get chat history for a session
    """
    # Verify session exists
    session = chat_session.get(db, id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get messages
    messages = chat_message.get_by_session(
        db,
        session_id=session_id,
        skip=offset,
        limit=limit
    )

    return messages


@router.delete("/chat/session/{session_id}")
async def clear_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Clear all messages in a session
    """
    session = chat_session.get(db, id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Delete all messages in session
    chat_message.delete_by_session(db, session_id=session_id)

    return {"message": "Session cleared successfully", "session_id": session_id}


@router.get("/chat/routes")
async def get_route_info() -> Dict[str, Any]:
    """
    Get information about available routes and their purposes
    """
    return {
        "routes": {
            "general-query": {
                "name": "日常对话",
                "description": "处理问候、寒暄等日常对话",
                "examples": ["你好", "谢谢", "今天天气不错"]
            },
            "additional-query": {
                "name": "补充信息",
                "description": "当问题模糊时，询问更多信息",
                "examples": ["我想做菜", "帮我推荐一道菜"]
            },
            "kb-query": {
                "name": "知识库查询",
                "description": "查询历史文化、典故等内容",
                "examples": ["宫保鸡丁的历史", "川菜的特点"]
            },
            "graphrag-query": {
                "name": "图谱查询",
                "description": "查询做法、食材、烹饪技巧",
                "examples": ["红烧肉怎么做", "需要什么食材"]
            },
            "text2sql-query": {
                "name": "统计查询",
                "description": "统计分析、计数、排名",
                "examples": ["有多少道菜", "最受欢迎的菜"]
            },
            "image-query": {
                "name": "图片处理",
                "description": "生成或分析图片",
                "examples": ["生成一张红烧肉的图片"]
            },
            "file-query": {
                "name": "文件处理",
                "description": "处理上传的菜谱文件",
                "examples": ["分析这个菜谱文档"]
            }
        },
        "auto_routing": "系统会根据您的问题自动选择合适的处理方式"
    }
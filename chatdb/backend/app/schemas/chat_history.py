from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    message_type: str
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    region: Optional[str] = None
    order_index: int


class ChatMessageCreate(ChatMessageBase):
    session_id: str


class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessage(ChatMessageBase):
    id: int
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: str
    connection_id: Optional[int] = None
    is_active: bool = True


class ChatSessionCreate(ChatSessionBase):
    id: str  # UUID格式


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    connection_id: Optional[int] = None
    is_active: Optional[bool] = None


class ChatSession(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True


class ChatHistorySnapshotBase(BaseModel):
    query: str
    response_data: Dict[str, Any]


class ChatHistorySnapshotCreate(ChatHistorySnapshotBase):
    session_id: str


class ChatHistorySnapshot(ChatHistorySnapshotBase):
    id: int
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """聊天历史响应模型 - 用于前端显示"""
    id: str
    title: str
    timestamp: datetime
    query: str
    response: Dict[str, Any]
    connection_id: Optional[int] = None


class ChatHistoryListResponse(BaseModel):
    """聊天历史列表响应"""
    sessions: List[ChatHistoryResponse]
    total: int
    page: int
    page_size: int


class SaveChatHistoryRequest(BaseModel):
    """保存聊天历史请求"""
    session_id: str
    title: str
    query: str
    response: Dict[str, Any]
    connection_id: Optional[int] = None


class RestoreChatHistoryResponse(BaseModel):
    """恢复聊天历史响应"""
    session_id: str
    title: str
    query: str
    response: Dict[str, Any]
    connection_id: Optional[int] = None
    created_at: datetime

"""
Pydantic schemas for chat history management.
Based on ChatDB implementation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Chat History Snapshot Schemas
class ChatHistorySnapshotCreate(BaseModel):
    """Schema for creating a new chat history snapshot."""

    conversation_id: int
    query: str
    response_data: Dict[str, Any]


class ChatHistorySnapshotResponse(BaseModel):
    """Schema for chat history snapshot response."""

    id: int
    conversation_id: int
    query: str
    response_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# Save Chat History Request
class SaveChatHistoryRequest(BaseModel):
    """Request to save chat history."""

    conversation_id: int
    title: str
    query: str
    response: Dict[str, Any]
    user_id: Optional[int] = None


# Chat History Response
class ChatHistoryResponse(BaseModel):
    """Response containing chat history."""

    id: int
    title: str
    timestamp: datetime
    query: str
    response: Dict[str, Any]
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# Chat History List Response
class ChatHistoryListResponse(BaseModel):
    """Response containing list of chat histories."""

    sessions: List[ChatHistoryResponse]
    total: int
    page: int
    page_size: int


# Restore Chat History Response
class RestoreChatHistoryResponse(BaseModel):
    """Response for restoring chat history."""

    conversation_id: int
    title: str
    query: str
    response: Dict[str, Any]
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

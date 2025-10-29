"""
Pydantic request/response models used by the HTTP API layer.

This package consolidates what used to live under ``gustobot.schemas`` so that the
name makes their purpose (API-facing contracts) explicit.
"""

from .chat import ChatRequest, ChatResponse
from .chat_history import (
    ConversationHistoryListResponse,
    ConversationHistoryResponse,
    ConversationHistorySnapshotCreate,
    ConversationHistorySnapshotResponse,
    RestoreConversationHistoryResponse,
    SaveConversationHistoryRequest,
)
from .chat_message import (
    ChatMessageBase,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageUpdate,
    ChatSessionSnapshotBase,
    ChatSessionSnapshotCreate,
    ChatSessionSnapshotResponse,
)
from .chat_session import ChatSessionBase, ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate
from .user import Token, UserBase, UserCreate, UserLogin, UserResponse, UserUpdate

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ChatMessageBase",
    "ChatMessageCreate",
    "ChatMessageUpdate",
    "ChatMessageResponse",
    "ChatSessionSnapshotBase",
    "ChatSessionSnapshotCreate",
    "ChatSessionSnapshotResponse",
    "ConversationHistorySnapshotCreate",
    "ConversationHistorySnapshotResponse",
    "ConversationHistoryResponse",
    "ConversationHistoryListResponse",
    "RestoreConversationHistoryResponse",
    "SaveConversationHistoryRequest",
    "ChatSessionBase",
    "ChatSessionCreate",
    "ChatSessionUpdate",
    "ChatSessionResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
]

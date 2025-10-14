"""
Database model representing a conversation window.
"""
from __future__ import annotations

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.logger import get_logger

logger = get_logger(service="conversation")


class DialogueType(enum.Enum):
    """Conversation type enumeration."""

    NORMAL = "普通对话"
    DEEP_THINKING = "深度思考"
    WEB_SEARCH = "联网检索"
    RAG = "RAG 问答"


class Conversation(Base):
    """Conversation model used to group message exchanges."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status = Column(String(20), default="ongoing")
    dialogue_type = Column(Enum(DialogueType), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title!r}>"

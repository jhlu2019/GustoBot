"""
Chat session models for persistent conversation storage.

Lightweight user ID system - no authentication, just user identification.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from gustobot.infrastructure.core.database import Base


class ChatSession(Base):
    """
    Chat session model for persistent conversation storage.

    Uses lightweight user ID system:
    - user_id is a string (device ID, UUID, etc.) provided by frontend
    - No User table or authentication required
    - Allows grouping sessions by user without login
    """

    __tablename__ = "chat_sessions"

    # Primary key - using UUID string for session ID
    id = Column(String(255), primary_key=True, index=True, comment="Session UUID")

    # Lightweight user identification (no FK, just a string)
    user_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="User identifier (device ID, anonymous UUID, etc.) - no authentication"
    )

    # Session metadata
    title = Column(
        String(500),
        nullable=False,
        comment="Session title (usually derived from first query)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Session creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment="Last update timestamp"
    )

    # Status flag for soft delete
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the session is active (soft delete flag)"
    )

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.order_index"
    )
    snapshots = relationship(
        "ChatSessionSnapshot",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatSessionSnapshot.created_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} title={self.title[:30]!r}>"

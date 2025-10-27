"""
Chat message model for storing individual messages within a session.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ChatMessage(Base):
    """
    Chat message model for storing individual messages in a session.

    Stores structured message data including user queries, agent responses,
    SQL queries, visualizations, and other message types.
    """

    __tablename__ = "chat_messages"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Session relationship
    session_id = Column(
        String(255),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent session ID"
    )

    # Message type classification
    message_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Message type: user_query, agent_response, knowledge, error, etc."
    )

    # Message content
    content = Column(
        Text,
        nullable=False,
        comment="Message content text"
    )

    # Additional metadata (flexible JSON storage)
    message_metadata = Column(
        JSON,
        nullable=True,
        comment="Additional metadata: route info, confidence, sources, etc."
    )

    # Message ordering within session
    order_index = Column(
        Integer,
        nullable=False,
        comment="Message order within the session"
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Message creation timestamp"
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        content_preview = self.content[:50] if self.content else ""
        return f"<ChatMessage id={self.id} type={self.message_type} content={content_preview!r}>"


class ChatHistorySnapshot(Base):
    """
    Chat history snapshot for quick restoration of complete conversation context.

    Stores a complete snapshot of a conversation turn (query + full response)
    for efficient retrieval and display in UI.
    """

    __tablename__ = "chat_history_snapshots"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Session relationship
    session_id = Column(
        String(255),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent session ID"
    )

    # User query
    query = Column(
        Text,
        nullable=False,
        comment="Original user query"
    )

    # Complete response data
    response_data = Column(
        JSON,
        nullable=False,
        comment="Complete response data including answer, metadata, sources, etc."
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Snapshot creation timestamp"
    )

    # Relationships
    session = relationship("ChatSession", back_populates="snapshots")

    def __repr__(self) -> str:
        query_preview = self.query[:50] if self.query else ""
        return f"<ChatHistorySnapshot id={self.id} query={query_preview!r}>"

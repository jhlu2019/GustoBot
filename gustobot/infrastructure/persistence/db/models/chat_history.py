"""
Chat history models - snapshot functionality for conversation persistence.
Based on ChatDB implementation with adaptations for GustoBot.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from gustobot.infrastructure.core.database import Base


class ConversationHistorySnapshot(Base):
    """
    Chat history snapshot model for quick conversation restoration.

    Stores complete conversation state including query and full response data
    in JSON format for efficient retrieval and restoration.
    """

    __tablename__ = "conversation_history_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query = Column(Text, nullable=False)  # User's original query
    response_data = Column(JSON, nullable=False)  # Complete response data
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", backref="snapshots")

    def __repr__(self) -> str:
        return f"<ConversationHistorySnapshot id={self.id} conversation_id={self.conversation_id}>"

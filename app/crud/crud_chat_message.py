"""
CRUD operations for ChatMessage and ChatHistorySnapshot models.
"""
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.chat_message import ChatHistorySnapshot, ChatMessage
from app.schemas.chat_message import (
    ChatHistorySnapshotCreate,
    ChatMessageCreate,
    ChatMessageUpdate,
)


class CRUDChatMessage(CRUDBase[ChatMessage, ChatMessageCreate, ChatMessageUpdate]):
    """CRUD operations for ChatMessage model."""

    def get_by_session(
        self,
        db: Session,
        *,
        session_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get messages for a specific session, ordered by index.

        Args:
            db: Database session
            session_id: Parent session UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of messages ordered by order_index
        """
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(self.model.order_index)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest_by_session(
        self, db: Session, *, session_id: str
    ) -> Optional[ChatMessage]:
        """
        Get the most recent message in a session.

        Args:
            db: Database session
            session_id: Parent session UUID

        Returns:
            Latest message or None
        """
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.order_index))
            .first()
        )

    def create_batch(
        self,
        db: Session,
        *,
        messages: List[ChatMessageCreate]
    ) -> List[ChatMessage]:
        """
        Create multiple messages in a single transaction.

        Args:
            db: Database session
            messages: List of message creation data

        Returns:
            List of created message instances
        """
        db_messages = []
        for message_data in messages:
            db_message = self.model(**message_data.dict())
            db.add(db_message)
            db_messages.append(db_message)

        db.commit()
        for db_message in db_messages:
            db.refresh(db_message)
        return db_messages


class CRUDChatHistorySnapshot(
    CRUDBase[ChatHistorySnapshot, ChatHistorySnapshotCreate, None]
):
    """CRUD operations for ChatHistorySnapshot model."""

    def get_by_session(
        self, db: Session, *, session_id: str
    ) -> List[ChatHistorySnapshot]:
        """
        Get all snapshots for a session, ordered by creation time (newest first).

        Args:
            db: Database session
            session_id: Parent session UUID

        Returns:
            List of snapshots
        """
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.created_at))
            .all()
        )

    def get_latest_by_session(
        self, db: Session, *, session_id: str
    ) -> Optional[ChatHistorySnapshot]:
        """
        Get the most recent snapshot for a session.

        Args:
            db: Database session
            session_id: Parent session UUID

        Returns:
            Latest snapshot or None
        """
        return (
            db.query(self.model)
            .filter(self.model.session_id == session_id)
            .order_by(desc(self.model.created_at))
            .first()
        )


# Create singleton instances
chat_message = CRUDChatMessage(ChatMessage)
chat_history_snapshot = CRUDChatHistorySnapshot(ChatHistorySnapshot)

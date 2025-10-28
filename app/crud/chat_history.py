"""
CRUD operations for chat history snapshots.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.chat_message import ChatHistorySnapshot
from app.schemas.chat_history import ChatHistorySnapshotCreate


class ChatHistoryCRUD:
    """CRUD operations for ChatHistorySnapshot model."""

    def create(self, db: Session, *, obj_in: ChatHistorySnapshotCreate) -> ChatHistorySnapshot:
        """Create a new chat history snapshot."""
        db_obj = ChatHistorySnapshot(
            conversation_id=obj_in.conversation_id,
            query=obj_in.query,
            response_data=obj_in.response_data,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, *, id: int) -> Optional[ChatHistorySnapshot]:
        """Get a chat history snapshot by ID."""
        return db.query(ChatHistorySnapshot).filter(ChatHistorySnapshot.id == id).first()

    def get_by_conversation(
        self, db: Session, *, conversation_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatHistorySnapshot]:
        """Get all snapshots for a conversation."""
        return (
            db.query(ChatHistorySnapshot)
            .filter(ChatHistorySnapshot.conversation_id == conversation_id)
            .order_by(ChatHistorySnapshot.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest_by_conversation(
        self, db: Session, *, conversation_id: int
    ) -> Optional[ChatHistorySnapshot]:
        """Get the latest snapshot for a conversation."""
        return (
            db.query(ChatHistorySnapshot)
            .filter(ChatHistorySnapshot.conversation_id == conversation_id)
            .order_by(ChatHistorySnapshot.created_at.desc())
            .first()
        )

    def delete(self, db: Session, *, id: int) -> Optional[ChatHistorySnapshot]:
        """Delete a chat history snapshot."""
        obj = db.query(ChatHistorySnapshot).filter(ChatHistorySnapshot.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# Singleton instance
chat_history_crud = ChatHistoryCRUD()

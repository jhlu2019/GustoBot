"""
CRUD operations for conversations.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, DialogueType


class ConversationCRUD:
    """CRUD operations for Conversation model."""

    def create(
        self,
        db: Session,
        *,
        user_id: int,
        title: str,
        dialogue_type: DialogueType = DialogueType.RAG,
    ) -> Conversation:
        """Create a new conversation."""
        db_obj = Conversation(
            user_id=user_id,
            title=title,
            dialogue_type=dialogue_type,
            status="ongoing",
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, *, id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return db.query(Conversation).filter(Conversation.id == id).first()

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, db: Session, *, db_obj: Conversation, obj_in: dict) -> Conversation:
        """Update a conversation."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_activity(self, db: Session, *, conversation_id: int) -> Optional[Conversation]:
        """Update conversation activity timestamp."""
        conv = self.get(db, id=conversation_id)
        if conv:
            # SQLAlchemy will automatically update updated_at due to onupdate=func.now()
            db.add(conv)
            db.commit()
            db.refresh(conv)
        return conv

    def delete(self, db: Session, *, id: int) -> Optional[Conversation]:
        """Delete a conversation (soft delete by changing status)."""
        obj = db.query(Conversation).filter(Conversation.id == id).first()
        if obj:
            obj.status = "deleted"
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


# Singleton instance
conversation_crud = ConversationCRUD()

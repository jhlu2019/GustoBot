from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.crud.base import CRUDBase
from app.models.chat_history import ChatSession, ChatMessage, ChatHistorySnapshot
from app.schemas.chat_history import (
    ChatSessionCreate, ChatSessionUpdate,
    ChatMessageCreate, ChatMessageUpdate,
    ChatHistorySnapshotCreate
)


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    def get_by_user_sessions(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        connection_id: Optional[int] = None
    ) -> List[ChatSession]:
        """获取用户的聊天会话列表"""
        query = db.query(self.model).filter(self.model.is_active == True)
        
        if connection_id is not None:
            query = query.filter(self.model.connection_id == connection_id)
            
        return query.order_by(desc(self.model.updated_at)).offset(skip).limit(limit).all()

    def get_with_messages(self, db: Session, *, session_id: str) -> Optional[ChatSession]:
        """获取包含消息的会话"""
        return db.query(self.model).filter(
            and_(self.model.id == session_id, self.model.is_active == True)
        ).first()

    def update_activity(self, db: Session, *, session_id: str) -> Optional[ChatSession]:
        """更新会话活动时间"""
        session = db.query(self.model).filter(self.model.id == session_id).first()
        if session:
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session


class CRUDChatMessage(CRUDBase[ChatMessage, ChatMessageCreate, ChatMessageUpdate]):
    def get_by_session(
        self, 
        db: Session, 
        *, 
        session_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """获取会话的消息列表"""
        return db.query(self.model).filter(
            self.model.session_id == session_id
        ).order_by(self.model.order_index).offset(skip).limit(limit).all()

    def get_latest_by_session(self, db: Session, *, session_id: str) -> Optional[ChatMessage]:
        """获取会话的最新消息"""
        return db.query(self.model).filter(
            self.model.session_id == session_id
        ).order_by(desc(self.model.order_index)).first()

    def create_batch(
        self, 
        db: Session, 
        *, 
        messages: List[ChatMessageCreate]
    ) -> List[ChatMessage]:
        """批量创建消息"""
        db_messages = []
        for message_data in messages:
            db_message = self.model(**message_data.dict())
            db.add(db_message)
            db_messages.append(db_message)
        
        db.commit()
        for db_message in db_messages:
            db.refresh(db_message)
        return db_messages


class CRUDChatHistorySnapshot(CRUDBase[ChatHistorySnapshot, ChatHistorySnapshotCreate, None]):
    def get_by_session(self, db: Session, *, session_id: str) -> List[ChatHistorySnapshot]:
        """获取会话的历史快照"""
        return db.query(self.model).filter(
            self.model.session_id == session_id
        ).order_by(desc(self.model.created_at)).all()

    def get_latest_by_session(self, db: Session, *, session_id: str) -> Optional[ChatHistorySnapshot]:
        """获取会话的最新快照"""
        return db.query(self.model).filter(
            self.model.session_id == session_id
        ).order_by(desc(self.model.created_at)).first()


# 创建CRUD实例
chat_session = CRUDChatSession(ChatSession)
chat_message = CRUDChatMessage(ChatMessage)
chat_history_snapshot = CRUDChatHistorySnapshot(ChatHistorySnapshot)

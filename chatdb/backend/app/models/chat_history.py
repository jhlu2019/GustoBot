from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ChatSession(Base):
    """聊天会话模型"""
    id = Column(String(255), primary_key=True, index=True)  # UUID格式的会话ID
    title = Column(String(500), nullable=False)  # 会话标题（通常是第一个查询的摘要）
    connection_id = Column(Integer, ForeignKey("dbconnection.id"), nullable=True)  # 关联的数据库连接
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)  # 是否活跃

    # 关系
    connection = relationship("DBConnection", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """聊天消息模型"""
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chatsession.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # 'user_query', 'analysis', 'sql', 'explanation', 'data', 'visualization'
    content = Column(Text, nullable=False)  # 消息内容
    message_metadata = Column(JSON, nullable=True)  # 额外的元数据（如SQL结果、可视化配置等）
    region = Column(String(50), nullable=True)  # 对应的区域类型
    order_index = Column(Integer, nullable=False)  # 消息在会话中的顺序
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    session = relationship("ChatSession", back_populates="messages")


class ChatHistorySnapshot(Base):
    """聊天历史快照模型 - 用于快速恢复完整对话"""
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chatsession.id"), nullable=False)
    query = Column(Text, nullable=False)  # 用户原始查询
    response_data = Column(JSON, nullable=False)  # 完整的响应数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    session = relationship("ChatSession")

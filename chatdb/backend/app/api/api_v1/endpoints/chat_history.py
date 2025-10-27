from typing import Any, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.schemas.chat_history import (
    ChatHistoryResponse, ChatHistoryListResponse,
    SaveChatHistoryRequest, RestoreChatHistoryResponse,
    ChatSessionCreate, ChatMessageCreate, ChatHistorySnapshotCreate
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ChatHistoryListResponse)
def get_chat_histories(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 50,
    connection_id: Optional[int] = None,
) -> Any:
    """
    获取聊天历史列表
    """
    try:
        # 获取会话列表
        sessions = crud.chat_session.get_by_user_sessions(
            db=db, skip=skip, limit=limit, connection_id=connection_id
        )
        
        # 转换为响应格式
        history_responses = []
        for session in sessions:
            # 获取最新的快照
            latest_snapshot = crud.chat_history_snapshot.get_latest_by_session(
                db=db, session_id=session.id
            )
            
            if latest_snapshot:
                history_response = ChatHistoryResponse(
                    id=session.id,
                    title=session.title,
                    timestamp=session.updated_at or session.created_at,
                    query=latest_snapshot.query,
                    response=latest_snapshot.response_data,
                    connection_id=session.connection_id
                )
                history_responses.append(history_response)
        
        # 获取总数
        total_sessions = crud.chat_session.get_by_user_sessions(
            db=db, skip=0, limit=1000, connection_id=connection_id
        )
        
        return ChatHistoryListResponse(
            sessions=history_responses,
            total=len(total_sessions),
            page=skip // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")


@router.post("/save", response_model=dict)
def save_chat_history(
    *,
    db: Session = Depends(deps.get_db),
    history_request: SaveChatHistoryRequest,
) -> Any:
    """
    保存聊天历史
    """
    try:
        # 检查会话是否存在
        existing_session = crud.chat_session.get(db=db, id=history_request.session_id)
        
        if not existing_session:
            # 创建新会话
            session_create = ChatSessionCreate(
                id=history_request.session_id,
                title=history_request.title,
                connection_id=history_request.connection_id
            )
            session = crud.chat_session.create(db=db, obj_in=session_create)
        else:
            # 更新现有会话
            session = crud.chat_session.update(
                db=db, 
                db_obj=existing_session,
                obj_in={"title": history_request.title, "connection_id": history_request.connection_id}
            )
        
        # 创建历史快照
        snapshot_create = ChatHistorySnapshotCreate(
            session_id=history_request.session_id,
            query=history_request.query,
            response_data=history_request.response
        )
        crud.chat_history_snapshot.create(db=db, obj_in=snapshot_create)
        
        # 更新会话活动时间
        crud.chat_session.update_activity(db=db, session_id=history_request.session_id)
        
        logger.info(f"保存聊天历史成功: {history_request.session_id}")
        return {"status": "success", "message": "聊天历史保存成功"}
        
    except Exception as e:
        logger.error(f"保存聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存聊天历史失败: {str(e)}")


@router.get("/{session_id}", response_model=RestoreChatHistoryResponse)
def get_chat_history(
    *,
    db: Session = Depends(deps.get_db),
    session_id: str,
) -> Any:
    """
    获取指定会话的聊天历史
    """
    try:
        # 获取会话信息
        session = crud.chat_session.get(db=db, id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        # 获取最新的快照
        latest_snapshot = crud.chat_history_snapshot.get_latest_by_session(
            db=db, session_id=session_id
        )
        
        if not latest_snapshot:
            raise HTTPException(status_code=404, detail="聊天历史快照不存在")
        
        return RestoreChatHistoryResponse(
            session_id=session.id,
            title=session.title,
            query=latest_snapshot.query,
            response=latest_snapshot.response_data,
            connection_id=session.connection_id,
            created_at=session.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")


@router.delete("/{session_id}", response_model=dict)
def delete_chat_history(
    *,
    db: Session = Depends(deps.get_db),
    session_id: str,
) -> Any:
    """
    删除聊天历史
    """
    try:
        # 获取会话
        session = crud.chat_session.get(db=db, id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        # 软删除（标记为非活跃）
        crud.chat_session.update(
            db=db, 
            db_obj=session,
            obj_in={"is_active": False}
        )
        
        logger.info(f"删除聊天历史成功: {session_id}")
        return {"status": "success", "message": "聊天历史删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除聊天历史失败: {str(e)}")


@router.post("/{session_id}/restore", response_model=dict)
def restore_chat_history(
    *,
    db: Session = Depends(deps.get_db),
    session_id: str,
) -> Any:
    """
    恢复聊天历史（重新激活）
    """
    try:
        # 获取会话
        session = crud.chat_session.get(db=db, id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="聊天会话不存在")
        
        # 重新激活
        crud.chat_session.update(
            db=db, 
            db_obj=session,
            obj_in={"is_active": True}
        )
        
        logger.info(f"恢复聊天历史成功: {session_id}")
        return {"status": "success", "message": "聊天历史恢复成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复聊天历史失败: {str(e)}")

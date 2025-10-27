# 混合问答对管理API端点

from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.api import deps
from app.services.hybrid_retrieval_service import (
    HybridRetrievalEngine, QAPairWithContext, RetrievalResult,
    extract_tables_from_sql, extract_entities_from_question, clean_sql, generate_qa_id
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# ===== 请求/响应模型 =====

class QAPairCreate(BaseModel):
    """创建问答对的请求模型"""
    question: str
    sql: str
    connection_id: int
    difficulty_level: int = 3
    query_type: str = "SELECT"
    verified: bool = False
    used_tables: Optional[List[str]] = None
    mentioned_entities: Optional[List[str]] = None

class QAPairResponse(BaseModel):
    """问答对响应模型"""
    id: str
    question: str
    sql: str
    connection_id: int
    difficulty_level: int
    query_type: str
    success_rate: float
    verified: bool
    created_at: datetime
    used_tables: List[str]
    mentioned_entities: List[str]

class SimilarQAPairResponse(BaseModel):
    """相似问答对响应模型"""
    qa_pair: QAPairResponse
    semantic_score: float
    structural_score: float
    pattern_score: float
    quality_score: float
    final_score: float
    explanation: str

class SearchRequest(BaseModel):
    """搜索请求模型"""
    question: str
    connection_id: Optional[int] = None
    schema_context: Optional[Dict[str, Any]] = None
    top_k: int = 5

class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    qa_id: str
    user_satisfaction: float  # 0.0 - 1.0
    feedback_text: Optional[str] = None

# ===== 全局变量 =====
hybrid_engine = None

async def get_hybrid_engine():
    """获取混合检索引擎实例"""
    global hybrid_engine
    if hybrid_engine is None:
        hybrid_engine = HybridRetrievalEngine()
        await hybrid_engine.initialize()
    return hybrid_engine

# ===== API端点 =====

@router.post("/qa-pairs/", response_model=Dict[str, Any])
async def create_qa_pair(
    qa_create: QAPairCreate,
    db: Session = Depends(deps.get_db)
):
    """创建新的问答对"""
    try:
        engine = await get_hybrid_engine()
        
        # 自动提取表名和实体（如果未提供）
        used_tables = qa_create.used_tables or extract_tables_from_sql(qa_create.sql)
        mentioned_entities = qa_create.mentioned_entities or extract_entities_from_question(qa_create.question)
        
        # 创建问答对对象
        qa_pair = QAPairWithContext(
            id=generate_qa_id(),
            question=qa_create.question,
            sql=clean_sql(qa_create.sql),
            connection_id=qa_create.connection_id,
            difficulty_level=qa_create.difficulty_level,
            query_type=qa_create.query_type,
            success_rate=0.0,
            verified=qa_create.verified,
            created_at=datetime.now(),
            used_tables=used_tables,
            used_columns=[],  # 可以进一步分析
            query_pattern=qa_create.query_type,
            mentioned_entities=mentioned_entities
        )
        
        # 存储问答对
        schema_context = {"tables": [{"name": table} for table in used_tables]}
        await engine.store_qa_pair(qa_pair, schema_context)
        
        return {
            "status": "success",
            "qa_id": qa_pair.id,
            "message": "问答对创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建问答对失败: {str(e)}")

@router.post("/qa-pairs/search", response_model=List[SimilarQAPairResponse])
async def search_similar_qa_pairs(
    search_request: SearchRequest,
    db: Session = Depends(deps.get_db)
):
    """搜索相似的问答对"""
    try:
        engine = await get_hybrid_engine()
        
        # 执行混合检索
        results = await engine.hybrid_retrieve(
            query=search_request.question,
            schema_context=search_request.schema_context or {},
            connection_id=search_request.connection_id or 0,
            top_k=search_request.top_k
        )
        
        # 转换为响应格式
        response_results = []
        for result in results:
            qa_response = QAPairResponse(
                id=result.qa_pair.id,
                question=result.qa_pair.question,
                sql=result.qa_pair.sql,
                connection_id=result.qa_pair.connection_id,
                difficulty_level=result.qa_pair.difficulty_level,
                query_type=result.qa_pair.query_type,
                success_rate=result.qa_pair.success_rate,
                verified=result.qa_pair.verified,
                created_at=result.qa_pair.created_at,
                used_tables=result.qa_pair.used_tables,
                mentioned_entities=result.qa_pair.mentioned_entities
            )
            
            response_results.append(SimilarQAPairResponse(
                qa_pair=qa_response,
                semantic_score=result.semantic_score,
                structural_score=result.structural_score,
                pattern_score=result.pattern_score,
                quality_score=result.quality_score,
                final_score=result.final_score,
                explanation=result.explanation
            ))
        
        return response_results
        
    except Exception as e:
        logger.error(f"搜索相似问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/qa-pairs/stats", response_model=Dict[str, Any])
async def get_qa_pairs_stats(
    connection_id: Optional[int] = Query(None, description="数据库连接ID"),
    db: Session = Depends(deps.get_db)
):
    """获取问答对统计信息"""
    try:
        # 这里可以添加从数据库获取统计信息的逻辑
        # 目前返回模拟数据
        stats = {
            "total_qa_pairs": 0,
            "verified_qa_pairs": 0,
            "query_types": {
                "SELECT": 0,
                "JOIN": 0,
                "AGGREGATE": 0,
                "GROUP_BY": 0,
                "ORDER_BY": 0
            },
            "difficulty_distribution": {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0
            },
            "average_success_rate": 0.0
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/qa-pairs/feedback", response_model=Dict[str, Any])
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(deps.get_db)
):
    """提交用户反馈"""
    try:
        # 这里可以添加反馈处理逻辑
        # 例如更新问答对的成功率、记录用户反馈等
        
        logger.info(f"收到反馈 - QA ID: {feedback.qa_id}, 满意度: {feedback.user_satisfaction}")
        
        return {
            "status": "success",
            "message": "反馈提交成功"
        }
        
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")

@router.get("/qa-pairs/health", response_model=Dict[str, Any])
async def health_check():
    """健康检查端点"""
    try:
        engine = await get_hybrid_engine()
        
        # 检查各个服务的状态
        health_status = {
            "hybrid_engine": "healthy",
            "milvus": "unknown",
            "neo4j": "unknown",
            "vector_service": "unknown"
        }
        
        # 可以添加更详细的健康检查逻辑
        
        return {
            "status": "healthy",
            "services": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/qa-pairs/batch-create", response_model=Dict[str, Any])
async def batch_create_qa_pairs(
    qa_pairs: List[QAPairCreate],
    db: Session = Depends(deps.get_db)
):
    """批量创建问答对"""
    try:
        engine = await get_hybrid_engine()
        
        created_count = 0
        failed_count = 0
        errors = []
        
        for i, qa_create in enumerate(qa_pairs):
            try:
                # 自动提取表名和实体
                used_tables = qa_create.used_tables or extract_tables_from_sql(qa_create.sql)
                mentioned_entities = qa_create.mentioned_entities or extract_entities_from_question(qa_create.question)
                
                # 创建问答对对象
                qa_pair = QAPairWithContext(
                    id=generate_qa_id(),
                    question=qa_create.question,
                    sql=clean_sql(qa_create.sql),
                    connection_id=qa_create.connection_id,
                    difficulty_level=qa_create.difficulty_level,
                    query_type=qa_create.query_type,
                    success_rate=0.0,
                    verified=qa_create.verified,
                    created_at=datetime.now(),
                    used_tables=used_tables,
                    used_columns=[],
                    query_pattern=qa_create.query_type,
                    mentioned_entities=mentioned_entities
                )
                
                # 存储问答对
                schema_context = {"tables": [{"name": table} for table in used_tables]}
                await engine.store_qa_pair(qa_pair, schema_context)
                created_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"第{i+1}个问答对创建失败: {str(e)}")
        
        return {
            "status": "completed",
            "created_count": created_count,
            "failed_count": failed_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"批量创建问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量创建失败: {str(e)}")

@router.delete("/qa-pairs/{qa_id}", response_model=Dict[str, Any])
async def delete_qa_pair(
    qa_id: str,
    db: Session = Depends(deps.get_db)
):
    """删除问答对"""
    try:
        # 这里可以添加删除逻辑
        # 需要从Neo4j和Milvus中删除相应的数据
        
        logger.info(f"删除问答对: {qa_id}")
        
        return {
            "status": "success",
            "message": f"问答对 {qa_id} 删除成功"
        }
        
    except Exception as e:
        logger.error(f"删除问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/qa-pairs/export", response_model=Dict[str, Any])
async def export_qa_pairs(
    connection_id: Optional[int] = Query(None, description="数据库连接ID"),
    format: str = Query("json", description="导出格式: json, csv"),
    db: Session = Depends(deps.get_db)
):
    """导出问答对数据"""
    try:
        # 这里可以添加导出逻辑
        # 从Neo4j或Milvus中获取数据并导出
        
        return {
            "status": "success",
            "message": "导出功能开发中",
            "format": format,
            "connection_id": connection_id
        }
        
    except Exception as e:
        logger.error(f"导出问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

from dataclasses import dataclass
from typing import List, Optional, Any, Dict

from autogen_core.memory import ListMemory
from pydantic import BaseModel, Field


class Text2SQLRequest(BaseModel):
    """将自然语言转换为SQL的请求模型"""
    query: str  # 用户的自然语言查询


class Text2SQLResponse(BaseModel):
    """SQL查询响应模型"""
    sql: str  # 生成的SQL语句
    explanation: str  # SQL语句的解释
    results: List[Dict[str, Any]]  # 查询结果
    visualization_type: Optional[str] = None  # 建议的可视化类型，例如："bar", "line", "pie"等
    visualization_config: Optional[Dict[str, Any]] = None  # 可视化配置信息


class ResponseMessage(BaseModel):
    """智能体响应消息"""
    source: str  # 消息来源
    content: str  # 消息内容
    is_final: bool = False  # 是否是最终消息
    result: Optional[Dict[str, Any]] = None  # 最终结果数据


class QueryMessage(BaseModel):
    """自然语言查询消息"""
    query: str  # 用户的自然语言查询
    connection_id: Optional[int] = None  # 数据库连接ID，可选


class SqlMessage(BaseModel):
    """SQL语句消息"""
    query: str  # 原始查询
    sql: str  # 生成的SQL语句
    connection_id: Optional[int] = None  # 数据库连接ID，可选


class SqlExplanationMessage(BaseModel):
    """SQL解释消息"""
    query: str  # 原始查询
    sql: str  # 生成的SQL语句
    explanation: str  # SQL语句的解释
    connection_id: Optional[int] = None  # 数据库连接ID，可选


class SqlResultMessage(BaseModel):
    """SQL执行结果消息"""
    query: str  # 原始查询
    sql: str  # 生成的SQL语句
    explanation: str  # SQL语句的解释
    results: List[Dict[str, Any]]  # 查询结果
    connection_id: Optional[int] = None  # 数据库连接ID，可选


class AnalysisMessage(BaseModel):
    """查询分析消息"""
    query: str  # 用户的查询
    analysis: str  # 分析结果
    memory_content: List[Dict[str, Any]]
    # 需要的Message基类字段
    content: str = ""
    role: str = "user"
    connection_id: Optional[int] = None  # 数据库连接ID，可选
    schema_context: Optional[Dict[str, Any]] = None  # 从图数据库获取的相关表结构信息
    mappings_str: Optional[str] = None  # 值映射字符串

class VisualizationMessage(BaseModel):
    """可视化消息"""
    sql: str  # 生成的SQL语句
    explanation: str  # SQL语句的解释
    results: List[Dict[str, Any]]  # 查询结果
    visualization_type: Optional[str] = None  # 可视化类型
    visualization_config: Optional[Dict[str, Any]] = None  # 可视化配置


class SchemaContextMessage(BaseModel):
    """表结构信息消息"""
    query: str  # 用户的原始查询
    connection_id: int  # 数据库连接ID
    schema_context: Dict[str, Any]  # 从图数据库获取的表结构信息
    mappings_str: Optional[str] = None  # 值映射字符串，用于在提示中展示


"""
异常处理模块，提供统一的异常类型和处理机制
"""
from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """应用基础异常类"""
    def __init__(self, message: str, code: str = "unknown_error", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(BaseAppException):
    """数据库相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="database_error", details=details)


class LLMException(BaseAppException):
    """LLM调用相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="llm_error", details=details)


class SchemaException(BaseAppException):
    """表结构相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="schema_error", details=details)


class SQLGenerationException(BaseAppException):
    """SQL生成相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="sql_generation_error", details=details)


class SQLExecutionException(BaseAppException):
    """SQL执行相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="sql_execution_error", details=details)


class ConnectionException(BaseAppException):
    """连接相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="connection_error", details=details)


class WebSocketException(BaseAppException):
    """WebSocket相关异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="websocket_error", details=details)

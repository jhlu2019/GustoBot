"""
SQL execution node.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from gustobot.config import settings
from gustobot.infrastructure.core.database import SessionLocal
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="text2sql.sql_execution")


def create_sql_execution_node(
    connection_string: Optional[str] = None,
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Build a LangGraph node that executes read-only SQL statements.
    """

    async def execute_sql(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("-----开始执行 SQL 查询-----")

        sql_statement = (state.get("sql_statement") or "").strip()
        connection_id = state.get("connection_id")
        max_rows = int(state.get("max_rows") or 1000)

        if not sql_statement:
            logger.warning("SQL 语句为空，跳过执行")
            return {
                "execution_results": None,
                "execution_error": "SQL 语句为空",
                "steps": ["sql_execution_skipped"],
            }

        if not _is_read_only_query(sql_statement):
            logger.warning("检测到非只读查询，已阻止执行")
            return {
                "execution_results": None,
                "execution_error": "仅支持只读 SELECT 查询",
                "steps": ["sql_execution_blocked"],
            }

        if not state.get("is_valid"):
            logger.warning("SQL 验证未通过，跳过执行")
            return {
                "execution_results": None,
                "execution_error": "SQL 验证未通过",
                "steps": ["sql_execution_skipped_invalid"],
            }

        conn_str = connection_string or _get_connection_string(connection_id)
        if not conn_str:
            logger.error("无法获取数据库连接信息 connection_id=%s", connection_id)
            return {
                "execution_results": None,
                "execution_error": "无法获取数据库连接信息",
                "steps": ["sql_execution_failed"],
            }

        try:
            results = await _execute_sql_query(conn_str, sql_statement, max_rows=max_rows)
            logger.info("SQL 执行成功，返回 %d 行结果", len(results))
            return {
                "execution_results": results,
                "execution_error": None,
                "steps": ["sql_execution"],
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("SQL 执行失败: %s", exc)
            return {
                "execution_results": None,
                "execution_error": str(exc),
                "steps": ["sql_execution_failed"],
            }

    return execute_sql


def _map_db_type_to_driver(db_type: str) -> str:
    mapping = {
        "mysql": "mysql+pymysql",
        "mariadb": "mysql+pymysql",
        "postgresql": "postgresql+psycopg2",
        "postgres": "postgresql+psycopg2",
        "pg": "postgresql+psycopg2",
        "sqlite": "sqlite",
    }
    return mapping.get((db_type or "").lower(), db_type)


def _get_connection_string(connection_id: Optional[int]) -> Optional[str]:
    """
    直接返回 MySQL 连接字符串，不再支持 SQLite 和 dbconnection 表查询。
    简化实现，统一使用 MySQL 作为 Text2SQL 的目标数据库。
    """
    logger.debug("使用默认 MySQL 数据库 URL: %s", settings.DATABASE_URL)
    return settings.DATABASE_URL


async def _execute_sql_query(
    connection_string: str,
    sql: str,
    max_rows: int = 1000,
) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(_run_query_sync, connection_string, sql, max_rows)


def _run_query_sync(
    connection_string: str,
    sql: str,
    max_rows: int,
) -> List[Dict[str, Any]]:
    engine: Engine = create_engine(connection_string, future=True)
    try:
        with engine.connect() as connection:
            result = connection.execution_options(stream_results=True).execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchmany(max_rows)
            return [
                {column: row[idx] for idx, column in enumerate(columns)}
                for row in rows
            ]
    finally:
        engine.dispose()


def _is_read_only_query(sql: str) -> bool:
    statement = sql.strip()
    if not statement:
        return False

    if ";" in statement.rstrip(";"):
        return False

    upper = statement.upper()
    return upper.startswith("SELECT ") or upper.startswith("WITH ")

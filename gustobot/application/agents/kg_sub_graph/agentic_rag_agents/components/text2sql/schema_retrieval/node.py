"""
Schema retrieval node.

Fetches tables, columns, and relationships directly from MySQL INFORMATION_SCHEMA.
简化实现，不再依赖 Neo4j，直接从 MySQL 数据库读取表结构。
"""
from __future__ import annotations

import re
from typing import Any, Callable, Coroutine, Dict, Iterable, List, Set, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from gustobot.config import settings
from gustobot.infrastructure.core.logger import get_logger
from ..domain_knowledge import (
    COLUMN_DESCRIPTIONS,
    RELATIONSHIP_FACTS,
    TABLE_DESCRIPTIONS,
)

logger = get_logger(service="text2sql.schema_retrieval")

_STOP_WORDS: Set[str] = {
    "the",
    "and",
    "for",
    "from",
    "with",
    "into",
    "what",
    "which",
    "when",
    "who",
    "where",
    "how",
    "many",
    "much",
    "that",
    "this",
    "those",
    "these",
    "all",
    "any",
    "year",
    "month",
    "day",
    "query",
    "please",
    "show",
    "list",
    "give",
    "查询",
    "一下",
    "所有",
    "哪些",
    "什么",
    "数据",
}


def create_schema_retrieval_node(
    neo4j_graph=None,  # 保留参数以兼容旧代码，但不再使用
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Build a LangGraph node that enriches the workflow state with schema
    metadata from MySQL INFORMATION_SCHEMA.
    """

    async def retrieve_schema(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("-----开始检索数据库 Schema (直接从 MySQL)-----")

        question = (state.get("question") or "").strip()

        try:
            schema_context = await _retrieve_schema_from_mysql(question)

            logger.info(
                "Schema 检索完成，匹配到 %d 张表", len(schema_context.get("tables", []))
            )

            return {
                "schema_context": schema_context,
                "value_mappings": {},  # 简化实现，不再使用值映射
                "mappings_str": "",
                "steps": ["schema_retrieval"],
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Schema 检索失败: %s", exc)
            return {
                "schema_context": {},
                "value_mappings": {},
                "mappings_str": "",
                "steps": ["schema_retrieval_failed"],
            }

    return retrieve_schema


def _extract_keywords(question: str) -> List[str]:
    if not question:
        return []

    tokens = re.findall(r"[a-zA-Z0-9_]+", question.lower())
    return [token for token in tokens if token and token not in _STOP_WORDS]


def _score_table(table: Dict[str, Any], keywords: Iterable[str]) -> float:
    if not keywords:
        return 0.0

    score = 0.0
    name = (table.get("table_name") or "").lower()
    description = (table.get("description") or "").lower()

    for kw in keywords:
        if kw in name:
            score += 2.0
        if kw in description:
            score += 1.0

    for column in table.get("columns", []):
        column_name = (column.get("column_name") or "").lower()
        column_desc = (column.get("description") or "").lower()
        for kw in keywords:
            if kw in column_name:
                score += 1.5
            if kw in column_desc:
                score += 0.75

    return score


async def _retrieve_schema_from_mysql(question: str) -> Dict[str, Any]:
    """
    直接从 MySQL INFORMATION_SCHEMA 读取表结构信息。
    """
    import asyncio

    def _sync_retrieve():
        engine: Engine = create_engine(settings.DATABASE_URL, future=True)
        try:
            with engine.connect() as conn:
                # 获取所有表信息
                tables_query = text("""
                    SELECT
                        TABLE_NAME,
                        TABLE_COMMENT
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """)
                table_rows = conn.execute(tables_query).fetchall()

                tables: List[Dict[str, Any]] = []

                for table_row in table_rows:
                    table_name = table_row[0]
                    table_comment = table_row[1] or ""
                    table_key = table_name.lower()

                    # 使用领域知识库补充描述
                    table_description = table_comment or TABLE_DESCRIPTIONS.get(table_key) or ""

                    # 获取列信息
                    columns_query = text("""
                        SELECT
                            COLUMN_NAME,
                            DATA_TYPE,
                            COLUMN_COMMENT,
                            COLUMN_KEY
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = :table_name
                        ORDER BY ORDINAL_POSITION
                    """)
                    column_rows = conn.execute(columns_query, {"table_name": table_name}).fetchall()

                    columns: List[Dict[str, Any]] = []
                    for col_row in column_rows:
                        column_name = col_row[0]
                        data_type = col_row[1]
                        column_comment = col_row[2] or ""
                        column_key = col_row[3]

                        # 使用领域知识库补充描述
                        column_desc_key = (table_key, column_name.lower())
                        column_description = column_comment or COLUMN_DESCRIPTIONS.get(column_desc_key) or ""

                        columns.append({
                            "column_name": column_name,
                            "data_type": data_type,
                            "description": column_description,
                            "is_primary_key": column_key == "PRI",
                            "is_foreign_key": column_key in ("MUL", "FK"),
                            "is_unique": column_key == "UNI",
                        })

                    tables.append({
                        "table_name": table_name,
                        "description": table_description,
                        "columns": columns,
                    })

                # 获取外键关系
                fk_query = text("""
                    SELECT
                        kcu.TABLE_NAME as source_table,
                        kcu.COLUMN_NAME as source_column,
                        kcu.REFERENCED_TABLE_NAME as target_table,
                        kcu.REFERENCED_COLUMN_NAME as target_column
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                    WHERE kcu.TABLE_SCHEMA = DATABASE()
                    AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
                    ORDER BY kcu.TABLE_NAME, kcu.COLUMN_NAME
                """)
                fk_rows = conn.execute(fk_query).fetchall()

                relationships: List[Dict[str, Any]] = []
                seen_keys: Set[Tuple[str, str, str, str]] = set()

                for fk_row in fk_rows:
                    key = (fk_row[0], fk_row[1], fk_row[2], fk_row[3])
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    relationships.append({
                        "source_table": fk_row[0],
                        "source_column": fk_row[1],
                        "target_table": fk_row[2],
                        "target_column": fk_row[3],
                        "relationship_type": "FOREIGN_KEY",
                        "description": f"{fk_row[0]}.{fk_row[1]} references {fk_row[2]}.{fk_row[3]}",
                    })

                # 添加领域知识关系
                table_name_lookup = {t["table_name"].lower(): t["table_name"] for t in tables}
                for relationship in RELATIONSHIP_FACTS:
                    source_lower = relationship["source_table"].lower()
                    target_lower = relationship["target_table"].lower()
                    if source_lower not in table_name_lookup or target_lower not in table_name_lookup:
                        continue

                    source_name = table_name_lookup[source_lower]
                    target_name = table_name_lookup[target_lower]

                    key = (
                        source_name,
                        relationship["source_column"],
                        target_name,
                        relationship["target_column"],
                    )
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    relationships.append({
                        "source_table": source_name,
                        "source_column": relationship["source_column"],
                        "target_table": target_name,
                        "target_column": relationship["target_column"],
                        "relationship_type": relationship.get("relationship_type", ""),
                        "description": relationship.get("description", ""),
                    })

                return tables, relationships
        finally:
            engine.dispose()

    # 在线程池中执行同步查询
    tables, relationships = await asyncio.to_thread(_sync_retrieve)

    # 根据问题关键词过滤表
    keywords = _extract_keywords(question)
    if keywords:
        scored_tables = [(table, _score_table(table, keywords)) for table in tables]
        positive = [item for item in scored_tables if item[1] > 0]
        if positive:
            positive.sort(key=lambda item: item[1], reverse=True)
            max_tables = 6
            tables = [item[0] for item in positive[:max_tables]]

            # 过滤关系，只保留相关表的关系
            table_names = {table["table_name"] for table in tables}
            relationships = [
                rel for rel in relationships
                if rel["source_table"] in table_names and rel["target_table"] in table_names
            ]

    schema_context = {
        "tables": tables,
        "relationships": relationships,
    }
    return schema_context

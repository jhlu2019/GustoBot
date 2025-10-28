"""
Schema retrieval node.

Fetches tables, columns, relationships, and optional value mappings
from Neo4j for a given database connection.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, Iterable, List, Set, Tuple

from langchain_neo4j import Neo4jGraph

from app.core.logger import get_logger
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
    neo4j_graph: Neo4jGraph,
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Build a LangGraph node that enriches the workflow state with schema
    metadata from Neo4j.
    """

    async def retrieve_schema(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("-----开始检索数据库 Schema-----")

        question = (state.get("question") or "").strip()
        connection_id = state.get("connection_id")

        if not connection_id:
            logger.warning("未提供 connection_id，跳过 Schema 检索")
            return {
                "schema_context": {},
                "value_mappings": {},
                "mappings_str": "",
                "steps": ["schema_retrieval_skipped"],
            }

        try:
            schema_context, column_lookup = await _retrieve_schema_from_neo4j(
                neo4j_graph,
                int(connection_id),
                question,
            )
            value_mappings = await _retrieve_value_mappings(
                neo4j_graph,
                int(connection_id),
                column_lookup,
            )
            mappings_str = _format_value_mappings_as_string(value_mappings)

            logger.info(
                "Schema 检索完成，匹配到 %d 张表", len(schema_context.get("tables", []))
            )

            return {
                "schema_context": schema_context,
                "value_mappings": value_mappings,
                "mappings_str": mappings_str,
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


async def _retrieve_schema_from_neo4j(
    graph: Neo4jGraph,
    connection_id: int,
    question: str,
) -> Tuple[Dict[str, Any], Dict[int, Tuple[str, str]]]:
    params = {"connection_id": connection_id}

    table_records = graph.query(
        """
        MATCH (t:Table {connection_id: $connection_id})
        OPTIONAL MATCH (t)-[:HAS_COLUMN]->(c:Column {connection_id: $connection_id})
        RETURN t { .id, .name, .description } AS table,
               collect(c { .id, .name, .type, .description, .is_pk, .is_fk, .is_unique }) AS columns
        ORDER BY toLower(t.name)
        """,
        params=params,
    ) or []

    tables: List[Dict[str, Any]] = []
    column_lookup: Dict[int, Tuple[str, str]] = {}

    for record in table_records:
        table_info = record.get("table") or {}
        table_id = table_info.get("id")
        table_name = table_info.get("name") or table_info.get("table_name")
        if not table_name:
            continue
        table_key = table_name.lower()
        table_description = (
            table_info.get("description")
            or TABLE_DESCRIPTIONS.get(table_key)
            or ""
        )

        columns_raw = record.get("columns") or []
        columns: List[Dict[str, Any]] = []

        for column in columns_raw:
            column_id = column.get("id")
            column_name = column.get("name") or column.get("column_name")
            if not column_name:
                continue
            column_key = (table_key, column_name.lower())
            column_description = (
                column.get("description")
                or COLUMN_DESCRIPTIONS.get(column_key)
                or ""
            )

            column_entry = {
                "column_id": column_id,
                "column_name": column_name,
                "data_type": column.get("type") or column.get("data_type") or "",
                "description": column_description,
                "is_primary_key": bool(column.get("is_pk") or column.get("is_primary_key")),
                "is_foreign_key": bool(column.get("is_fk") or column.get("is_foreign_key")),
                "is_unique": bool(column.get("is_unique", False)),
            }
            columns.append(column_entry)

            if column_id is not None:
                column_lookup[column_id] = (table_name, column_name)

        tables.append(
            {
                "table_id": table_id,
                "table_name": table_name,
                "description": table_description,
                "columns": columns,
            }
        )

    keywords = _extract_keywords(question)
    if keywords:
        scored_tables = [(table, _score_table(table, keywords)) for table in tables]
        positive = [item for item in scored_tables if item[1] > 0]
        if positive:
            positive.sort(key=lambda item: item[1], reverse=True)
            max_tables = 6
            tables = [item[0] for item in positive[:max_tables]]
            kept_column_ids = {
                column["column_id"]
                for table in tables
                for column in table.get("columns", [])
                if column.get("column_id") is not None
            }
            column_lookup = {
                column_id: lookup
                for column_id, lookup in column_lookup.items()
                if column_id in kept_column_ids
            }

    table_names = {table["table_name"] for table in tables}
    table_name_lookup = {table["table_name"].lower(): table["table_name"] for table in tables}

    relationship_records = graph.query(
        """
        MATCH (source:Column {connection_id: $connection_id})-[r:REFERENCES]->(target:Column {connection_id: $connection_id})
        MATCH (source_table:Table {connection_id: $connection_id})-[:HAS_COLUMN]->(source)
        MATCH (target_table:Table {connection_id: $connection_id})-[:HAS_COLUMN]->(target)
        RETURN source_table.name AS source_table,
               source.name AS source_column,
               target_table.name AS target_table,
               target.name AS target_column,
               coalesce(r.type, '') AS relationship_type,
               coalesce(r.description, '') AS description
        """,
        params=params,
    ) or []

    relationships: List[Dict[str, Any]] = []
    seen_keys: Set[Tuple[str, str, str, str]] = set()

    for record in relationship_records:
        source_table = record.get("source_table")
        target_table = record.get("target_table")
        if table_names and (
            source_table not in table_names or target_table not in table_names
        ):
            continue

        key = (
            source_table or "",
            record.get("source_column") or "",
            target_table or "",
            record.get("target_column") or "",
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)

        relationships.append(
            {
                "source_table": source_table,
                "source_column": record.get("source_column"),
                "target_table": target_table,
                "target_column": record.get("target_column"),
                "relationship_type": record.get("relationship_type") or "",
                "description": record.get("description") or "",
            }
        )

    # Ensure domain factual relationships are present even if Neo4j metadata lacks them.
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
        relationships.append(
            {
                "source_table": source_name,
                "source_column": relationship["source_column"],
                "target_table": target_name,
                "target_column": relationship["target_column"],
                "relationship_type": relationship.get("relationship_type", ""),
                "description": relationship.get("description", ""),
            }
        )

    schema_context = {
        "tables": tables,
        "relationships": relationships,
    }
    return schema_context, column_lookup


async def _retrieve_value_mappings(
    graph: Neo4jGraph,
    connection_id: int,
    column_lookup: Dict[int, Tuple[str, str]],
) -> Dict[str, Dict[str, str]]:
    if not column_lookup:
        return {}

    try:
        records = graph.query(
            """
            MATCH (c:Column {connection_id: $connection_id})
            OPTIONAL MATCH (c)-[:HAS_VALUE_MAPPING]->(m:ValueMapping)
            WHERE m IS NOT NULL
            RETURN c.id AS column_id,
                   collect(m { .nl_term, .db_value }) AS mappings
            """,
            params={"connection_id": connection_id},
        ) or []
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("获取值映射失败: %s", exc)
        return {}

    value_mappings: Dict[str, Dict[str, str]] = defaultdict(dict)

    for record in records:
        column_id = record.get("column_id")
        if column_id is None:
            continue

        table_column = column_lookup.get(column_id)
        if not table_column:
            continue

        table_name, column_name = table_column
        mapping_key = f"{table_name}.{column_name}"

        for mapping in record.get("mappings") or []:
            nl_term = mapping.get("nl_term")
            db_value = mapping.get("db_value")
            if nl_term and db_value:
                value_mappings[mapping_key][str(nl_term)] = str(db_value)

    return dict(value_mappings)


def _format_value_mappings_as_string(value_mappings: Dict[str, Dict[str, str]]) -> str:
    if not value_mappings:
        return ""

    lines = ["-- Value Mappings:"]
    for column, mappings in value_mappings.items():
        if not mappings:
            continue
        lines.append(f"-- For {column}:")
        for nl_term, db_value in mappings.items():
            lines.append(
                f"--   '{nl_term}' in natural language refers to '{db_value}' in the database"
            )
    lines.append("")
    return "\n".join(lines)

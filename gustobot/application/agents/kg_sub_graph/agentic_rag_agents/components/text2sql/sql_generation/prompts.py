"""
Prompt templates for SQL generation.
"""
from __future__ import annotations

from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate

from ..domain_knowledge import COLUMN_DESCRIPTIONS, DOMAIN_SUMMARY, TABLE_DESCRIPTIONS


def create_sql_generation_prompt() -> ChatPromptTemplate:
    system_message = """
你是一名资深 SQL 开发工程师。请根据提供的数据库 Schema、值映射信息和查询分析结果，生成符合 {db_type} 语法的 SQL 查询。

约束条件：
1. 只使用提供的表与字段。
2. 严格遵循查询分析给出的意图、筛选条件、连接方式等，如需调整请在最终解释中说明。
3. 使用值映射信息将自然语言术语转换为数据库中的真实值。
4. 输出必须是**单条 SQL 语句**，不能包含额外解释或多条语句。
5. 默认只生成只读查询（SELECT/CTE）。
"""
    system_message = (
        system_message.strip()
        + "\n\n数据库真实结构背景：\n"
        + DOMAIN_SUMMARY
    )

    human_message = """
## 数据库 Schema
```sql
{schema}
```

## 值映射
{value_mappings}

## 查询分析摘要
{analysis_summary}

## 用户问题
{question}

请输出最终 SQL 语句。
"""

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_message.strip()),
            ("human", human_message.strip()),
        ]
    )


def format_schema_as_text(schema_context: Dict[str, any]) -> str:
    """
    Convert schema context into a SQL-like textual description for prompting.
    """
    if not schema_context or not schema_context.get("tables"):
        return "-- No schema information available"

    lines: List[str] = []

    for table in schema_context.get("tables", []):
        table_name = table.get("table_name", "unknown_table")
        table_key = table_name.lower()
        description = table.get("description") or TABLE_DESCRIPTIONS.get(table_key) or ""

        lines.append(f"-- Table: {table_name}")
        if description:
            lines.append(f"-- Description: {description}")

        lines.append(f"CREATE TABLE {table_name} (")
        columns = table.get("columns", [])
        for index, column in enumerate(columns):
            column_name = column.get("column_name", "col")
            data_type = column.get("data_type", "TEXT")
            column_key = (table_key, column_name.lower())
            column_description = column.get("description") or COLUMN_DESCRIPTIONS.get(column_key) or ""
            column_constraints: List[str] = []
            if column.get("is_primary_key"):
                column_constraints.append("PRIMARY KEY")
            if column.get("is_foreign_key"):
                column_constraints.append("FOREIGN KEY")
            if column.get("is_unique"):
                column_constraints.append("UNIQUE")

            constraint_str = f" {' '.join(column_constraints)}" if column_constraints else ""
            comma = "," if index < len(columns) - 1 else ""
            lines.append(f"    {column_name} {data_type}{constraint_str}{comma}")
            if column_description:
                lines.append(f"    -- {column_description}")

        lines.append(");")
        lines.append("")

    relationships = schema_context.get("relationships") or []
    if relationships:
        lines.append("-- Table Relationships")
        for rel in relationships:
            source_table = rel.get("source_table")
            source_column = rel.get("source_column")
            target_table = rel.get("target_table")
            target_column = rel.get("target_column")
            relationship_type = rel.get("relationship_type", "N/A")
            description = rel.get("description") or ""
            lines.append(
                f"-- {source_table}.{source_column} -> {target_table}.{target_column} ({relationship_type})"
            )
            if description:
                lines.append(f"--   {description}")

    return "\n".join(lines)

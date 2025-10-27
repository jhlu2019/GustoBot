"""
Utility helpers for Text2SQL workflows.
"""
from __future__ import annotations

from typing import Optional

from app.agents.text2sql.models import SQLAnalysis


def render_analysis_markdown(
    analysis: Optional[SQLAnalysis],
    fallback_text: Optional[str] = None,
) -> str:
    """
    Render a human-readable analysis summary. Falls back to the raw text
    if structured data is not available.
    """
    if not analysis:
        return fallback_text or ""

    lines = ["## SQL 命令分析报告"]

    if analysis.query_intent:
        lines.append("\n### 1. 查询意图")
        lines.append(analysis.query_intent)

    if analysis.required_tables:
        lines.append("\n### 2. 涉及的表")
        for table in analysis.required_tables:
            lines.append(f"- {table}")

    if analysis.required_columns:
        lines.append("\n### 3. 关键字段")
        for column in analysis.required_columns:
            lines.append(f"- {column}")

    if analysis.join_conditions:
        lines.append("\n### 4. 连接关系")
        lines.append(analysis.join_conditions)

    if analysis.filter_conditions:
        lines.append("\n### 5. 筛选条件")
        lines.append(analysis.filter_conditions)

    if analysis.aggregation:
        lines.append("\n### 6. 聚合需求")
        lines.append(analysis.aggregation)

    if analysis.order_by:
        lines.append("\n### 7. 排序要求")
        lines.append(analysis.order_by)

    if analysis.notes:
        lines.append("\n### 8. 其它说明")
        lines.append(analysis.notes)

    rendered = "\n".join(lines).strip()
    if rendered:
        return rendered
    return fallback_text or ""

"""
SQL generation node.
"""
from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from app.agents.text2sql.utils import render_analysis_markdown
from app.core.logger import get_logger

from ..schema_retrieval.node import _format_value_mappings_as_string
from .prompts import create_sql_generation_prompt, format_schema_as_text

logger = get_logger(service="text2sql.sql_generation")


def create_sql_generation_node(
    llm: BaseChatModel,
    db_type: str = "MySQL",
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Build a LangGraph node that generates SQL statements from the analysed query.
    """
    prompt = create_sql_generation_prompt()
    sql_llm = llm.with_config(temperature=0.1)
    sql_chain = prompt | sql_llm | StrOutputParser()

    async def generate_sql(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("-----开始生成 SQL 语句-----")

        schema_context = state.get("schema_context") or {}
        value_mappings = state.get("value_mappings") or {}
        analysis_dict = state.get("analysis")
        analysis_text = state.get("analysis_text") or ""

        if not schema_context:
            logger.warning("缺少 Schema 信息，无法生成 SQL")
            return {
                "sql_statement": "",
                "steps": ["sql_generation_failed_no_schema"],
            }

        schema_text = format_schema_as_text(schema_context)
        mappings_str = _format_value_mappings_as_string(value_mappings)
        analysis_summary = analysis_text or render_analysis_markdown(analysis_dict, "")

        question = state.get("question", "")
        inputs = {
            "db_type": db_type,
            "schema": schema_text,
            "value_mappings": mappings_str or "无值映射信息",
            "analysis_summary": analysis_summary or "无分析信息",
            "question": question,
        }

        try:
            sql_raw = await sql_chain.ainvoke(inputs)
            sql_statement = _clean_sql_statement(sql_raw)
            logger.info("SQL 生成完成")
            return {
                "sql_statement": sql_statement,
                "steps": ["sql_generation"],
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("SQL 生成失败: %s", exc)
            return {
                "sql_statement": "",
                "steps": ["sql_generation_failed"],
            }

    return generate_sql


def _clean_sql_statement(sql: str) -> str:
    """
    Remove Markdown code fences and normalise whitespace.
    """
    cleaned = sql.replace("```sql", "").replace("```", "").strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(lines)

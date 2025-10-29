"""
Query analysis node.
"""
from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel

from app.agents.text2sql.models import SQLAnalysis
from app.agents.text2sql.utils import render_analysis_markdown
from app.core.logger import get_logger

from ..sql_generation.prompts import format_schema_as_text
from .prompts import create_query_analysis_prompt

logger = get_logger(service="text2sql.query_analysis")


def create_query_analysis_node(
    llm: BaseChatModel,
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """Build a LangGraph node that performs structured query analysis."""

    prompt = create_query_analysis_prompt()
    analysis_chain = prompt | llm.with_structured_output(SQLAnalysis)

    async def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("-----开始分析查询意图-----")

        question = state.get("question", "")
        schema_context = state.get("schema_context") or {}
        # value_mappings 功能已简化移除
        mappings_str = ""

        schema_text = format_schema_as_text(schema_context)

        inputs = {
            "db_type": state.get("db_type", "MySQL"),
            "schema": schema_text,
            "value_mappings": mappings_str or "无值映射信息",
            "question": question,
        }

        analysis: SQLAnalysis = await analysis_chain.ainvoke(inputs)
        analysis_dict = analysis.model_dump()
        rendered_markdown = render_analysis_markdown(analysis, None)

        logger.info(
            "查询分析完成，涉及表：%s", ", ".join(analysis.required_tables or [])
        )

        return {
            "analysis": analysis_dict,
            "analysis_text": rendered_markdown,
            "steps": ["query_analysis"],
        }

    return analyze

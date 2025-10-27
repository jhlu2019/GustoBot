"""
Text2SQL Workflow built on LangGraph.

The workflow mirrors the multi-agent responsibilities from ChatDB,
implemented as LangGraph nodes:
1. Schema retrieval (Neo4j)
2. Query analysis
3. SQL generation
4. SQL validation / retry loop
5. SQL execution
6. Visualization recommendation
7. Answer formatting
"""
from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.graph import END, START, StateGraph

from app.core.logger import get_logger

from .components import (
    create_answer_formatter_node,
    create_query_analysis_node,
    create_schema_retrieval_node,
    create_sql_execution_node,
    create_sql_generation_node,
    create_sql_validation_node,
    create_visualization_node,
)
from .state import Text2SQLInputState, Text2SQLState, Text2SQLOutputState

logger = get_logger(service="text2sql.workflow")


def create_text2sql_workflow(
    llm: BaseChatModel,
    neo4j_graph: Neo4jGraph,
    db_type: str = "MySQL",
    connection_string: str | None = None,
    max_retries: int = 3,
) -> StateGraph:
    """
    Assemble the Text2SQL workflow.
    """
    logger.info("创建 Text2SQL 工作流")

    retrieve_schema = create_schema_retrieval_node(neo4j_graph)
    analyze_query = create_query_analysis_node(llm)
    generate_sql = create_sql_generation_node(llm, db_type)
    validate_sql = create_sql_validation_node(db_type)
    execute_sql = create_sql_execution_node(connection_string)
    recommend_viz = create_visualization_node(llm)
    format_answer = create_answer_formatter_node()

    builder = StateGraph(
        Text2SQLState,
        input=Text2SQLInputState,
        output=Text2SQLOutputState,
    )

    builder.add_node("retrieve_schema", retrieve_schema)
    builder.add_node("analyze_query", analyze_query)
    builder.add_node("generate_sql", generate_sql)
    builder.add_node("validate_sql", validate_sql)
    builder.add_node("execute_sql", execute_sql)
    builder.add_node("visualization", recommend_viz)
    builder.add_node("format_answer", format_answer)

    builder.add_edge(START, "retrieve_schema")
    builder.add_edge("retrieve_schema", "analyze_query")
    builder.add_edge("analyze_query", "generate_sql")
    builder.add_edge("generate_sql", "validate_sql")

    builder.add_conditional_edges(
        "validate_sql",
        _should_execute_or_retry,
        {
            "execute": "execute_sql",
            "retry": "generate_sql",
            "end": "format_answer",
        },
    )

    builder.add_edge("execute_sql", "visualization")
    builder.add_edge("visualization", "format_answer")
    builder.add_edge("format_answer", END)

    graph = builder.compile()
    graph.config["max_retries"] = max_retries
    return graph


def _should_execute_or_retry(state: Text2SQLState) -> Literal["execute", "retry", "end"]:
    """
    Decide whether to execute the SQL, retry generation, or end the workflow.
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if is_valid:
        return "execute"
    if retry_count < max_retries:
        logger.warning("SQL 验证失败，准备第 %d 次重试", retry_count + 1)
        return "retry"

    logger.error("达到最大重试次数，终止工作流")
    return "end"


__all__ = ["create_text2sql_workflow"]

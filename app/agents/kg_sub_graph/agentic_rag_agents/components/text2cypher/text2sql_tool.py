"""
Text2SQL tool wrapper for the multi-tool workflow.

This node bridges the planner/tool-selection workflow with the
Text2SQL LangGraph pipeline implemented under ``app.agents.text2sql``.
"""
from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, List, Optional

from langchain_openai import ChatOpenAI

from app.agents.kg_sub_graph.agentic_rag_agents.components.cypher_tools.node import (
    CypherQueryOutputState,
)
from app.agents.text2sql import create_text2sql_workflow
from app.config import settings
from app.core.logger import get_logger

try:  # Lazy import to avoid circular dependency when Neo4j is unavailable.
    from app.agents.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph
except Exception:  # pragma: no cover - defensive
    get_neo4j_graph = None  # type: ignore

logger = get_logger(service="text2sql-tool")


def create_text2sql_tool_node(
    neo4j_graph=None,
) -> Callable[[Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Create a LangGraph node that executes the Text2SQL workflow.

    Parameters
    ----------
    neo4j_graph : Neo4jGraph | None
        Existing Neo4j graph connection used for schema retrieval. If ``None``,
        the node will attempt to obtain one via ``get_neo4j_graph``.
    """

    async def text2sql_query(state: Dict[str, Any]) -> Dict[str, Any]:
        question = state.get("task") or state.get("question") or ""
        tool_args: Dict[str, Any] = state.get("query_parameters", {}) or {}

        connection_id = tool_args.get("connection_id")
        db_type = tool_args.get("db_type") or "MySQL"
        max_rows = int(tool_args.get("max_rows") or 1000)
        connection_string = tool_args.get("connection_string")
        max_retries = int(tool_args.get("max_retries") or 3)

        errors: List[str] = []

        graph = neo4j_graph
        if graph is None and get_neo4j_graph is not None:
            try:
                graph = get_neo4j_graph()
                logger.info("Obtained Neo4j graph connection for Text2SQL tool.")
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to obtain Neo4j graph connection: %s", exc)
                errors.append(f"无法连接图数据库: {exc}")
                graph = None

        if graph is None:
            answer = "抱歉，当前无法连接图数据库，暂时不能执行数据库查询。"
            records_payload = {
                "answer": answer,
                "rows": [],
                "sql": "",
            }
            return {
                "cyphers": [
                    CypherQueryOutputState(
                        **{
                            "task": question,
                            "query": "",
                            "errors": errors or ["图数据库连接不可用"],
                            "records": records_payload,
                            "steps": ["execute_text2sql_query"],
                        }
                    )
                ],
                "summary": answer,
                "steps": ["execute_text2sql_query"],
            }

        if not settings.OPENAI_API_KEY:
            answer = "抱歉，系统暂时无法调用模型执行数据库查询，请稍后再试。"
            records_payload = {
                "answer": answer,
                "rows": [],
                "sql": "",
            }
            return {
                "cyphers": [
                    CypherQueryOutputState(
                        **{
                            "task": question,
                            "query": "",
                            "errors": errors + ["OPENAI_API_KEY 未配置"],
                            "records": records_payload,
                            "steps": ["execute_text2sql_query"],
                        }
                    )
                ],
                "summary": answer,
                "steps": ["execute_text2sql_query"],
            }

        text2sql_llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=0.0,
            tags=["text2sql"],
        )

        workflow = create_text2sql_workflow(
            llm=text2sql_llm,
            neo4j_graph=graph,
            db_type=db_type,
            connection_string=connection_string,
            max_retries=max_retries,
        )
        workflow.config["max_rows"] = max_rows

        input_state = {
            "question": question,
            "connection_id": connection_id,
            "db_type": db_type,
            "max_retries": max_retries,
            "max_rows": max_rows,
        }

        try:
            result: Dict[str, Any] = await workflow.ainvoke(input_state)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Text2SQL workflow execution failed: %s", exc)
            error_message = f"执行数据库查询失败：{exc}"
            errors.append(error_message)
            answer = "抱歉，执行数据库查询时发生异常，请稍后再试。"
            records_payload = {
                "answer": answer,
                "rows": [],
                "sql": "",
                "error": error_message,
            }
            return {
                "cyphers": [
                    CypherQueryOutputState(
                        **{
                            "task": question,
                            "query": "",
                            "errors": errors,
                            "records": records_payload,
                            "steps": ["execute_text2sql_query"],
                        }
                    )
                ],
                "summary": answer,
                "steps": ["execute_text2sql_query"],
            }

        answer = result.get("answer") or ""
        sql_statement = result.get("sql_statement") or ""
        execution_results = result.get("execution_results") or []
        execution_error = result.get("execution_error")
        visualization = result.get("visualization")
        viz_config = result.get("visualization_config")

        if execution_error:
            errors.append(str(execution_error))

        records_payload = {
            "answer": answer,
            "rows": execution_results,
            "sql": sql_statement,
            "visualization": visualization,
        }
        if viz_config:
            records_payload["visualization_config"] = viz_config

        return {
            "cyphers": [
                CypherQueryOutputState(
                    **{
                        "task": question,
                        "query": sql_statement,
                        "errors": errors,
                        "records": records_payload,
                        "steps": ["execute_text2sql_query"],
                    }
                )
            ],
            "summary": answer or None,
            "steps": ["execute_text2sql_query"],
        }

    return text2sql_query


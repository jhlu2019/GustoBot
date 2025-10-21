from typing import Any, Callable, Coroutine, Dict, List
import re

from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

from app.agents.kg_sub_graph.agentic_rag_agents.constants import NO_CYPHER_RESULTS
from app.agents.kg_sub_graph.agentic_rag_agents.components.state import PredefinedCypherInputState
from app.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.state import CypherOutputState
from app.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.utils import create_vector_query_matcher
from app.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.descriptions import QUERY_DESCRIPTIONS
from app.config import settings


def create_predefined_cypher_node(
    graph: Neo4jGraph, predefined_cypher_dict: Dict[str, str]
) -> Callable[
    [PredefinedCypherInputState],
    Coroutine[Any, Any, Dict[str, List[CypherOutputState] | List[str]]],
]:
    """
    Create a predefined Cypher execution node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    predefined_cypher_dict : Dict[str, str]
        A Python dictionary with Cypher query names as keys and parameterized Cypher queries as values.

    Returns
    -------
    Callable[[PredefinedCypherInputState], Dict[str, List[CypherOutputState] | List[str]]]
        The LangGraph node named `predefined_cypher`.
    """
    matcher = create_vector_query_matcher(predefined_cypher_dict, QUERY_DESCRIPTIONS)

    openai_kwargs: Dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0,
    }
    if settings.OPENAI_API_KEY:
        openai_kwargs["openai_api_key"] = settings.OPENAI_API_KEY
    if settings.OPENAI_API_BASE:
        openai_kwargs["openai_api_base"] = settings.OPENAI_API_BASE
    chat_llm = ChatOpenAI(**openai_kwargs)

    async def predefined_cypher(
        state: PredefinedCypherInputState,
    ) -> Dict[str, List[CypherOutputState] | List[str]]:
        """
        Executes a predefined Cypher statement with found parameters.
        """
        errors: List[str] = []

        question = state.get("task", "")
        incoming_params = state.get("query_parameters", {}) or {}
        query_name = incoming_params.get("query") or state.get("query_name", "")

        if not query_name:
            matches = matcher.match_query(question, top_k=1)
            if matches:
                query_name = matches[0]["query_name"]
            else:
                errors.append("无法为当前问题匹配到预定义查询。")

        statement = predefined_cypher_dict.get(query_name) if query_name else None
        parameters: Dict[str, Any] = incoming_params.get("parameters") or {}

        if statement and not parameters:
            parameters = matcher.extract_parameters(question, query_name, llm=chat_llm)

        # 确保参数类型为字符串键
        parameters = {str(k): v for k, v in parameters.items()}

        records: List[Dict[str, Any]] | List[str] = []
        if not statement:
            errors.append(f"未找到对应的 Cypher 模板：{query_name}")
        else:
            required_params = {name for name in re.findall(r"\$(\w+)", statement)}
            missing = [name for name in required_params if not parameters.get(name)]
            if missing:
                errors.append(f"缺少查询参数: {', '.join(missing)}")
            else:
                records = graph.query(query=statement, params=parameters) or []

        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", ""),
                        "statement": statement or "",
                        "parameters": {
                            "query": query_name,
                            "parameters": parameters,
                        },
                        "errors": errors,
                        "records": records if records else NO_CYPHER_RESULTS,
                        "steps": ["execute_predefined_cypher"],
                    }
                )
            ],
            "steps": ["execute_predefined_cypher"],
        }

    return predefined_cypher

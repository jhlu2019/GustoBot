"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.utils.utils import retrieve_and_parse_schema_from_graph_for_prompts
from gustobot.application.agents.kg_sub_graph.prompts.kg_prompts import GUARDRAILS_SYSTEM_PROMPT


def create_guardrails_prompt_template(
    graph: Optional[Neo4jGraph] = None, scope_description: Optional[str] = None
) -> ChatPromptTemplate:
    """
    Create a guardrails prompt template.

    Parameters
    ----------
    graph : Optional[Neo4jGraph], optional
        The `Neo4jGraph` object used to generated a schema definition, by default None
    scope_description : Optional[str], optional
        A description of the application scope, by default None

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    scope_context = (
        f"参考此范围描述来决策:\n{scope_description}"
        if scope_description is not None
        else ""
    )

    # 动态从 Neo4j 图表中获取图表结构
    graph_context = (
        f"\n参考图表结构来回答:\n{retrieve_and_parse_schema_from_graph_for_prompts(graph)}"
        if graph is not None
        else ""
    )

    message = scope_context + graph_context + "\nQuestion: {question}"

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                GUARDRAILS_SYSTEM_PROMPT,
            ),
            (
                "human",
                (message),
            ),
        ]
    )

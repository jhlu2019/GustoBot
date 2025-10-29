"""
Compatibility layer for legacy imports of the multi-tool workflow.

The project previously hosted an early draft of the recipe KG multi-tool agent
in this module. The implementation has since moved under
``gustobot.application.agents.kg_sub_graph.agentic_rag_agents``.  To avoid breaking existing
imports we re-export the canonical components and workflows from the new
package while keeping the public API identical.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools import (
    create_graphrag_query_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.cypher_tools import (
    create_cypher_query_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.errors import (
    create_error_tool_selection_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.final_answer import (
    create_final_answer_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.models import Task
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.planner import (
    create_planner_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher import (
    create_predefined_cypher_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.state import (
    CypherHistoryRecord,
    HistoryRecord,
    InputState,
    OverallState,
    OutputState,
    ToolSelectionErrorState,
    ToolSelectionInputState,
    ToolSelectionOutputState,
    update_history,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.summarize import (
    create_summarization_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.state import (
    CypherInputState,
    CypherOutputState,
    CypherState,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.text2sql_tool import (
    create_text2sql_tool_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.tool_selection import (
    create_tool_selection_node,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.base import (
    BaseCypherExampleRetriever,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.workflows.single_agent import (
    create_text2cypher_agent,
)
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.workflows.multi_agent.multi_tool import (
    create_kb_multi_tool_workflow as _agentic_create_kb_multi_tool_workflow,
    create_multi_tool_workflow as _agentic_create_multi_tool_workflow,
)

__all__ = [
    "create_multi_tool_workflow",
    "create_kb_multi_tool_workflow",
    "create_tool_selection_node",
    "create_error_tool_selection_node",
    "create_final_answer_node",
    "create_summarization_node",
    "create_planner_node",
    "create_cypher_query_node",
    "create_predefined_cypher_node",
    "create_text2cypher_agent",
    "create_text2sql_tool_node",
    "create_graphrag_query_node",
    "InputState",
    "OverallState",
    "OutputState",
    "ToolSelectionInputState",
    "ToolSelectionOutputState",
    "ToolSelectionErrorState",
    "CypherInputState",
    "CypherState",
    "CypherOutputState",
    "HistoryRecord",
    "CypherHistoryRecord",
    "Task",
    "update_history",
]


def create_multi_tool_workflow(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    tool_schemas: List[type[BaseModel]],
    predefined_cypher_dict: Dict[str, str],
    cypher_example_retriever: BaseCypherExampleRetriever,
    scope_description: Optional[str] = None,
    llm_cypher_validation: bool = True,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
    default_to_text2cypher: bool = True,
) -> CompiledStateGraph:
    """
    Backwards-compatible wrapper around the agentic multi-tool workflow.
    """

    return _agentic_create_multi_tool_workflow(
        llm=llm,
        graph=graph,
        tool_schemas=tool_schemas,
        predefined_cypher_dict=predefined_cypher_dict,
        cypher_example_retriever=cypher_example_retriever,
        scope_description=scope_description,
        llm_cypher_validation=llm_cypher_validation,
        max_attempts=max_attempts,
        attempt_cypher_execution_on_final_attempt=attempt_cypher_execution_on_final_attempt,
        default_to_text2cypher=default_to_text2cypher,
    )


def create_kb_multi_tool_workflow(
    llm: BaseChatModel,
    knowledge_service: Optional[Any] = None,
    *,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    filter_expr: Optional[str] = None,
    allow_external: Optional[bool] = None,
    external_search_url: Optional[str] = None,
    external_search_timeout: Optional[float] = None,
    scope_description: Optional[str] = None,
) -> CompiledStateGraph:
    """
    Backwards-compatible wrapper around the agentic KB workflow.
    """

    return _agentic_create_kb_multi_tool_workflow(
        llm=llm,
        knowledge_service=knowledge_service,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        filter_expr=filter_expr,
        allow_external=allow_external,
        external_search_url=external_search_url,
        external_search_timeout=external_search_timeout,
        scope_description=scope_description,
    )

"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph

from ..utils.utils import retrieve_and_parse_schema_from_graph_for_prompts
from app.agents.kg_sub_graph.prompts.kg_prompts import GUARDRAILS_SYSTEM_PROMPT
from app.agents.kg_sub_graph.prompts import create_guardrails_context

guardrails_system = """
You must decide whether the provided question is in scope.
Assume the question might be related.
If you're absolutely sure it is NOT related, output "end".
Provide only the specified output: "planner" or "end".
"""




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
    # 使用新的安全schema工具获取上下文
    context = create_guardrails_context(graph=graph, scope_description=scope_description)
    
    # 构建消息模板
    message = context["scope_context"] + context["graph_schema"] + "Question: {question}"

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
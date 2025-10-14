"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import Neo4jGraph

from ....components.text2cypher.correction.prompts import (
    create_text2cypher_correction_prompt_template,
)
from ..state import CypherState

correction_cypher_prompt = create_text2cypher_correction_prompt_template()


def create_text2cypher_correction_node(
    llm: BaseChatModel, graph: Neo4jGraph
) -> Callable[[CypherState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Text2Cypher query correction node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM to use for processing.
    graph : Neo4jGraph
        The Neo4j graph wrapper.

    Returns
    -------
    Callable[[CypherState], CypherState]
        The LangGraph node.
    """

    correct_cypher_chain = correction_cypher_prompt | llm | StrOutputParser()

    async def correct_cypher(state: CypherState) -> Dict[str, Any]:
        """
        Correct the Cypher statement based on the provided errors.
        """

        corrected_cypher = await correct_cypher_chain.ainvoke(
            {
                "question": state.get("task"),
                "errors": state.get("errors"),
                "cypher": state.get("statement"),
                "schema": graph.schema,
            }
        )

        return {
            "next_action_cypher": "validate_cypher",
            "statement": corrected_cypher,
            "steps": ["correct_cypher"],
        }

    return correct_cypher

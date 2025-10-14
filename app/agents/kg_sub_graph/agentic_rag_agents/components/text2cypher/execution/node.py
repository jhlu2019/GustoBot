"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

from langchain_neo4j import Neo4jGraph

from ....constants import NO_CYPHER_RESULTS
from ..state import CypherOutputState, CypherState


def create_text2cypher_execution_node(
    graph: Neo4jGraph,
) -> Callable[
    [CypherState], Coroutine[Any, Any, Dict[str, List[CypherOutputState] | List[str]]]
]:
    """
    Create a Text2Cypher execution node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.

    Returns
    -------
    Callable[[CypherState], Dict[str, List[CypherOutputState] | List[str]]]
        The LangGraph node.
    """

    async def execute_cypher(
        state: CypherState,
    ) -> Dict[str, List[CypherOutputState] | List[str]]:
        """
        Executes the given Cypher statement.
        """
        print("我现在进入到执行了")
        print("state", state)
        records = graph.query(state.get("statement", ""))
        print("records", records)
        steps = state.get("steps", list())
        steps.append("execute_cypher")
        
        print("我现在全部执行完了")
        print("state", state)

        ans = [
                CypherOutputState(
                    **{
                        "task": state.get("task", []),
                        "statement": state.get("statement", ""),
                        "parameters": None,
                        "errors": state.get("errors", list()),
                        "records": records if records else NO_CYPHER_RESULTS,
                        "steps": steps,
                    }
                )
            ]
        
        print("ans", ans)
       

        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", []),
                        "statement": state.get("statement", ""),
                        "parameters": None,
                        "errors": state.get("errors", list()),
                        "records": records if records else NO_CYPHER_RESULTS,
                        "steps": steps,
                    }
                )
            ],
            "steps": ["text2cypher"],
        }

    return execute_cypher

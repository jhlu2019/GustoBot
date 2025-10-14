from typing import Any, Callable, Coroutine, Dict, List

from langchain_neo4j import Neo4jGraph
from langchain_core.language_models import BaseChatModel

from app.agents.kg_sub_graph.agentic_rag_agents.constants import NO_CYPHER_RESULTS
from app.agents.kg_sub_graph.agentic_rag_agents.components.state import PredefinedCypherInputState
from app.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.state import CypherOutputState
from app.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.utils import create_vector_query_matcher
from app.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.descriptions import QUERY_DESCRIPTIONS


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
    async def predefined_cypher(
        state: PredefinedCypherInputState,
    ) -> Dict[str, List[CypherOutputState] | List[str]]:
        """
        Executes a predefined Cypher statement with found parameters.
        """
        errors = list()

        statement_name = state.get("query_name", "")
        params = state.get(
            "query_parameters", dict()
        )  

        statement = predefined_cypher_dict.get(params.get("query"))
   
        if statement is not None:
            records = graph.query(query=statement, params=params.get("parameters"))
            print(f"records: {records}")
            
        else:
            errors.append(
                f"Unable to find the specified Cypher statement: {statement_name}"
            )
            records = list()

        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", ""),
                        "statement": statement or "",
                        "parameters": params,
                        "errors": errors,
                        "records": records or NO_CYPHER_RESULTS,
                        "steps": ["execute_predefined_cypher"],
                    }
                )
            ],
            "steps": ["execute_predefined_cypher"],
        }

    return predefined_cypher

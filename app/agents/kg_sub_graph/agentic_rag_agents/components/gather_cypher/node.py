from typing import Any, Callable, Dict

from ...components.state import OverallState


def create_gather_cypher_node() -> Callable[[OverallState], Dict[str, Any]]:
    """
    Create a gather_cypher node for a LangGraph workflow.

    Returns
    -------
    Callable[[OverallState], OverallState]
        The LangGraph node.
    """

    def gather_cypher(state: OverallState) -> Dict[str, Any]:
        """
        Gather Cypher task results.
        """

        return {"steps": ["gather_cypher"]}

    return gather_cypher

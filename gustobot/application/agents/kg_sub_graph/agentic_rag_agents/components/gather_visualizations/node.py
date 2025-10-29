from typing import Any, Callable, Dict

from ...components.state import OverallState


def create_gather_visualizations_node() -> Callable[[OverallState], Dict[str, Any]]:
    """
    Create a gather_visualizations node for a LangGraph workflow.

    Returns
    -------
    Callable[[OverallState], OverallState]
        The LangGraph node.
    """

    def gather_visualizations(state: OverallState) -> Dict[str, Any]:
        """
        Gather visualization task results.
        """
        return {"steps": ["gather_visualizations"]}

    return gather_visualizations

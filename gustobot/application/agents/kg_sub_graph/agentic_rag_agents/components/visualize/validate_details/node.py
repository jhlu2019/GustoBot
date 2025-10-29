from typing import Any, Callable, Dict

from pydantic import ValidationError

from ....components.visualize.generate_details.models import ChartDetailsOutput
from ..state import VisualizationState


def create_validate_chart_details_node() -> (
    Callable[[VisualizationState], Dict[str, Any]]
):
    """
    Create a validate chart details node for a LangGraph workflow.

    Returns
    -------
    Callable[[VisualizationState], VisualizationState]
        The LangGraph node.
    """

    def validate_chart_details(state: VisualizationState) -> Dict[str, Any]:
        """
        validate the generated chart details.
        """

        errors = None
        keys = None
        records = state.get("records")

        if records and len(records) > 0:
            keys = list(records[0].keys())

        if keys is not None:
            try:
                ChartDetailsOutput.model_validate(
                    {
                        "title": state.get("title"),
                        "x_axis_key": state.get("x_axis_key"),
                        "y_axis_key": state.get("y_axis_key"),
                        "hue_key": state.get("hue_key"),
                        "chart_type": state.get("chart_type"),
                        "chart_description": state.get("chart_description"),
                    },
                    context={"keys": keys},
                )
            except ValidationError as e:
                errors = e.errors()

        if errors:
            next_action_visualization = "correct_chart_details"
        else:
            next_action_visualization = "generate_chart"

        return {
            "errors": errors,
            "next_action_visualization": next_action_visualization,
            "steps": ["validate_chart_details"],
        }

    return validate_chart_details

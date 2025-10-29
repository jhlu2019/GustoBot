from typing import Any, Callable, Coroutine, Dict, List

import pandas as pd

from ....components.visualize.generate_chart.charts import (
    create_bar_plot,
    create_empty_plot,
    create_line_plot,
    create_scatter_plot,
)
from ..state import VisualizationOutputState, VisualizationState


def create_chart_generation_node() -> (
    Callable[
        [VisualizationState],
        Coroutine[Any, Any, Dict[str, List[VisualizationOutputState] | List[str]]],
    ]
):
    """
    Create a chart generation node for a LangGraph workflow.

    Returns
    -------
    Callable[[VisualizationState], Dict[str, List[VisualizationOutputState] | List[str]]]
        The LangGraph node.
    """

    async def generate_chart(
        state: VisualizationState,
    ) -> Dict[str, List[VisualizationOutputState] | List[str]]:
        """
        Generate a chart based on the provided chart details.
        """

        viz_args = {
            "data": pd.DataFrame(state.get("records")),
            "x": state.get("x_axis_key"),
            "y": state.get("y_axis_key"),
            "hue": state.get("hue_key"),
        }
        match state.get("chart_type"):
            case "scatter":
                chart = create_scatter_plot(**viz_args)
            case "line":
                chart = create_line_plot(**viz_args)
            case "bar":
                chart = create_bar_plot(**viz_args)
            case _:
                chart = create_empty_plot()

        steps = state.get("steps", list())
        steps.append("generate_chart")

        return {
            "visualizations": [
                VisualizationOutputState(
                    **{
                        "task": state.get("task", ""),
                        "chart": chart,
                        "chart_description": state.get("chart_description", ""),
                        "steps": steps,
                    }
                )
            ],
            "steps": ["vizualize"],
        }

    return generate_chart

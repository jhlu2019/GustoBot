from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable

from ....components.visualize.correct_details.prompts import (
    create_correct_chart_details_prompt_template,
)
from ....components.visualize.generate_details.models import ChartDetailsOutput
from ..state import VisualizationState

correct_chart_details_prompt = create_correct_chart_details_prompt_template()


def create_correct_chart_details_node(
    llm: BaseChatModel,
) -> Callable[[VisualizationState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a chart details node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM do perform processing.

    Returns
    -------
    Callable[[CypherState], OutputState]
        The LangGraph node.
    """

    chart_details_chain: Runnable[Dict[str, Any], Any] = (
        correct_chart_details_prompt | llm.with_structured_output(ChartDetailsOutput)
    )

    async def correct_chart_details(state: VisualizationState) -> Dict[str, Any]:
        """
        Correct chart details.
        """

        chart_details: ChartDetailsOutput = await chart_details_chain.ainvoke(
            {
                "question": state.get("task"),
                "data": state.get("records"),
                "errors": state.get("errors"),
                "details": {
                    "title": state.get("title"),
                    "x_axis_key": state.get("x_axis_key"),
                    "y_axis_key": state.get("y_axis_key"),
                    "hue_key": state.get("hue_key"),
                    "chart_type": state.get("chart_type"),
                    "chart_description": state.get("chart_description"),
                },
            }
        )
        return {
            "title": chart_details.title,
            "x_axis_key": chart_details.x_axis_key,
            "y_axis_key": chart_details.y_axis_key,
            "hue_key": chart_details.hue_key,
            "chart_type": chart_details.chart_type,
            "chart_description": chart_details.chart_description,
            "steps": ["correct_chart_details"],
        }

    return correct_chart_details

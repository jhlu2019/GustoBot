from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable

from ....components.visualize.generate_details.models import ChartDetailsOutput
from ....components.visualize.generate_details.prompts import (
    create_chart_details_prompt_template,
)
from ..state import VisualizationInputState

generate_chart_details_prompt = create_chart_details_prompt_template()


def create_chart_details_node(
    llm: BaseChatModel,
) -> Callable[[VisualizationInputState], Coroutine[Any, Any, Dict[str, Any]]]:
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
        generate_chart_details_prompt | llm.with_structured_output(ChartDetailsOutput)
    )

    async def generate_chart_details(state: VisualizationInputState) -> Dict[str, Any]:
        """
        Generate chart details to be used for generating a chart visualization of the data.
        """

        chart_details: ChartDetailsOutput = await chart_details_chain.ainvoke(
            {"question": state.get("task"), "data": state.get("records")}
        )
        return {
            "title": chart_details.title,
            "x_axis_key": chart_details.x_axis_key,
            "y_axis_key": chart_details.y_axis_key,
            "chart_type": chart_details.chart_type,
            "chart_description": chart_details.chart_description,
            "steps": ["generate_chart_details"],
        }

    return generate_chart_details

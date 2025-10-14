from typing import Literal

from langchain_core.language_models import BaseChatModel
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from ...components.state import (
    OverallState,
)
from ...components.visualize import (
    create_chart_details_node,
    create_chart_generation_node,
    create_correct_chart_details_node,
    create_validate_chart_details_node,
)
from ...components.visualize.state import VisualizationInputState, VisualizationState


def create_visualization_agent(llm: BaseChatModel) -> CompiledStateGraph:
    """
    Create a visualization agent using LangGraph.
    This agent may be used as an independent workflow or a node in a larger LangGraph workflow.

    Returns
    -------
    CompiledStateGraph
        The workflow.
    """

    generate_chart_details = create_chart_details_node(llm=llm)
    validate_chart_details = create_validate_chart_details_node()
    correct_chart_details = create_correct_chart_details_node(llm=llm)
    generate_chart = create_chart_generation_node()

    g_builder = StateGraph(
        VisualizationState, input=VisualizationInputState, output=OverallState
    )
    g_builder.add_node(generate_chart_details)
    g_builder.add_node(validate_chart_details)
    g_builder.add_node(correct_chart_details)
    g_builder.add_node(generate_chart)

    g_builder.add_edge(START, "generate_chart_details")
    g_builder.add_edge("generate_chart_details", "validate_chart_details")
    g_builder.add_edge("correct_chart_details", "validate_chart_details")
    g_builder.add_conditional_edges(
        "validate_chart_details", validate_chart_details_conditional_edge
    )
    g_builder.add_edge("generate_chart", END)

    return g_builder.compile()


def validate_chart_details_conditional_edge(
    state: VisualizationState,
) -> Literal["correct_chart_details", "generate_chart", "__end__"]:
    match state.get("next_action_visualization"):
        case "correct_chart_details":
            return "correct_chart_details"
        case "generate_chart":
            return "generate_chart"
        case "__end__":
            return "__end__"
        case _:
            return "__end__"

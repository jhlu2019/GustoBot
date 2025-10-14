"""
This file contains classes that manage the state of a Visualization Agent or subgraph.
"""

from operator import add
from typing import Annotated, Any, Dict, List, Optional

from pydantic_core import ErrorDetails
from typing_extensions import TypedDict


class VisualizationInputState(TypedDict):
    task: str
    records: List[Dict[str, Any]]


class VisualizationState(TypedDict):
    task: str
    records: List[Dict[str, Any]]
    title: str
    x_axis_key: str
    y_axis_key: str
    hue_key: Optional[str]
    chart_type: str
    chart_description: str
    errors: List[ErrorDetails]
    next_action_visualization: str
    steps: Annotated[List[str], add]


class VisualizationOutputState(TypedDict):
    task: str
    chart: Any
    chart_description: str
    steps: List[str]

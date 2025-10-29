"""
This file contains classes that manage the state of a Visualization Agent or subgraph.
"""

from operator import add
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - prefer typing_extensions for Pydantic compatibility
    from typing_extensions import Annotated, TypedDict  # type: ignore
except ImportError:  # pragma: no cover - minimal stdlib fallback
    from typing import Annotated, TypedDict

from pydantic_core import ErrorDetails


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

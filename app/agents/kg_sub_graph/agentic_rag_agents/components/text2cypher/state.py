"""
This file contains classes that manage the state of a Text2Cypher Agent or subgraph.
"""

from operator import add
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - prefer typing_extensions for Pydantic compatibility
    from typing_extensions import Annotated, TypedDict  # type: ignore
except ImportError:  # pragma: no cover - minimal stdlib fallback
    from typing import Annotated, TypedDict


class CypherInputState(TypedDict):
    task: Annotated[list, add]


class CypherState(TypedDict):
    task: Annotated[list, add]
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    next_action_cypher: str
    attempts: int
    steps: Annotated[List[str], add]


class CypherOutputState(TypedDict):
    task: Annotated[list, add]
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    steps: List[str]

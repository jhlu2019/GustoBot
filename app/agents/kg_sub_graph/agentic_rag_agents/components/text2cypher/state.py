"""
This file contains classes that manage the state of a Text2Cypher Agent or subgraph.
"""

from operator import add
from typing import Annotated, Any, Dict, List, Optional

from typing_extensions import TypedDict


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

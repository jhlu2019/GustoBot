"""
TypedDict state definitions for crawler agent nodes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class CrawlerInputState(TypedDict, total=False):
    """Inputs required to run a crawler."""

    crawler_type: str
    crawler_options: Dict[str, Any]
    run_params: Dict[str, Any]
    context: Dict[str, Any]
    steps: List[str]


class CrawlerRunOutputState(TypedDict):
    """Payload produced after executing a crawler."""

    type: str
    raw_results: List[Dict[str, Any]]
    stats: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str]
    steps: List[str]


class CrawlerValidationOutputState(TypedDict):
    """Validated payload after running data verification."""

    type: str
    validated_items: List[Dict[str, Any]]
    rejected_items: int
    metadata: Dict[str, Any]
    errors: List[str]
    steps: List[str]

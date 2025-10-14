"""
State models for LangGraph workflow.
Uses TypedDict for better type safety and LangGraph integration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
from typing_extensions import NotRequired

from pydantic import BaseModel


class ConversationInput(BaseModel):
    """User request entering the supervisor workflow."""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ConversationState(TypedDict):
    """Mutable state passed between LangGraph nodes using TypedDict."""

    # Required fields
    message: str

    # Optional fields
    session_id: NotRequired[Optional[str]]
    user_id: NotRequired[Optional[str]]

    history: NotRequired[List[Dict[str, Any]]]
    cache_scope: NotRequired[Optional[str]]
    cache_messages: NotRequired[List[Dict[str, str]]]

    route: NotRequired[Optional[str]]
    confidence: NotRequired[float]
    reason: NotRequired[Optional[str]]

    answer: NotRequired[Optional[str]]
    answer_type: NotRequired[Optional[str]]
    metadata: NotRequired[Dict[str, Any]]

    cached: NotRequired[bool]
    error: NotRequired[Optional[str]]


class RouterResult(BaseModel):
    """Decision returned from the router node."""

    route: str
    confidence: float = 0.0
    reason: Optional[str] = None


class AgentAnswer(BaseModel):
    """Generic answer payload emitted by chat/knowledge nodes."""

    answer: str
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

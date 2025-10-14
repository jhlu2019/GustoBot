"""
Pydantic models describing agent inputs and shared state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationInput(BaseModel):
    """User request entering the supervisor workflow."""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ConversationState(BaseModel):
    """Mutable state passed between LangGraph nodes."""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    history: List[Dict[str, Any]] = Field(default_factory=list)
    cache_scope: Optional[str] = None
    cache_messages: List[Dict[str, str]] = Field(default_factory=list)

    route: Optional[str] = None
    confidence: float = 0.0
    reason: Optional[str] = None

    answer: Optional[str] = None
    answer_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    cached: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary for LangGraph."""
        return self.model_dump(exclude_none=True)


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

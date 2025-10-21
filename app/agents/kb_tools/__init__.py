"""
KG knowledge base agent module.

Exposes LangGraph-compatible nodes for querying the structured knowledge base.
"""

from .node import (
    KnowledgeQueryInputState,
    KnowledgeQueryOutputState,
    create_knowledge_query_node,
)
from .prompts import build_knowledge_system_prompt

__all__ = [
    "KnowledgeQueryInputState",
    "KnowledgeQueryOutputState",
    "create_knowledge_query_node",
    "build_knowledge_system_prompt",
]

"""
知识图谱提示词模块

提供统一的提示词管理功能，简化prompts的导入和使用
"""

from .kg_prompts import (
    PLANNER_SYSTEM_PROMPT,
    GUARDRAILS_SYSTEM_PROMPT,
    TEXT2CYPHER_GENERATION_PROMPT,
    TEXT2CYPHER_VALIDATION_PROMPT,
    SUMMARIZE_SYSTEM_PROMPT,
    FINAL_ANSWER_SYSTEM_PROMPT,
    PROMPT_MAPPING
)

from .schema_utils import (
    safe_get_schema,
    create_guardrails_context
)

__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "GUARDRAILS_SYSTEM_PROMPT",
    "TEXT2CYPHER_GENERATION_PROMPT",
    "TEXT2CYPHER_VALIDATION_PROMPT", 
    "SUMMARIZE_SYSTEM_PROMPT",
    "FINAL_ANSWER_SYSTEM_PROMPT",
    "PROMPT_MAPPING",
    "safe_get_schema",
    "create_guardrails_context"
] 
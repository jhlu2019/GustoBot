from typing import Optional, TypedDict

from langchain_core.messages import ToolCall


class ToolSelectionOutputState(TypedDict):
    tool_selection_task: str
    tool_call: Optional[ToolCall]
    next_action: str

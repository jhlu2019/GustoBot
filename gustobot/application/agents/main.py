import sys
import os
from pathlib import Path
from typing import List, Optional, Sequence

# 将项目根目录添加到 Python 路径
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from gustobot.application.agents.lg_states import InputState
from gustobot.application.agents.utils import new_uuid
from gustobot.application.agents.lg_builder import graph
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import RemoveMessage
from langgraph.types import Command
import asyncio
import time
import builtins

thread = {"configurable": {"thread_id": new_uuid()}}


def _resolve_memory_turn_limit() -> Optional[int]:
    """Resolve configured memory turns, treating non-positive values as unlimited."""
    raw_value = os.getenv("GUSTOBOT_MEMORY_TURNS", os.getenv("GUSTOBOT_MAX_MEMORY_TURNS", "2"))
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        value = 5
    return value if value > 0 else None


MEMORY_TURN_LIMIT: Optional[int] = _resolve_memory_turn_limit()


def _select_messages_to_remove(existing: Sequence[BaseMessage]) -> List[BaseMessage]:
    """Determine which historical messages should be dropped to respect the turn limit."""
    if not existing or MEMORY_TURN_LIMIT is None:
        return []

    humans_to_keep = max(MEMORY_TURN_LIMIT - 1, 0)
    if humans_to_keep == 0:
        return [msg for msg in existing if getattr(msg, "id", None)]

    humans_seen = 0
    keep_from = 0
    for index in range(len(existing) - 1, -1, -1):
        message = existing[index]
        if getattr(message, "type", None) == "human":
            humans_seen += 1
            if humans_seen == humans_to_keep:
                keep_from = index
                break
    else:
        keep_from = 0

    return [msg for msg in existing[:keep_from] if getattr(msg, "id", None)]


def _stringify_content(content: object) -> str:
    """Convert streamed message content into printable text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


async def process_query(query: str) -> None:
    state_snapshot = graph.get_state(thread)
    existing_messages = list(state_snapshot.values.get("messages", []))
    messages_to_remove = _select_messages_to_remove(existing_messages)

    removals = [
        RemoveMessage(id=msg.id)
        for msg in messages_to_remove
        if getattr(msg, "id", None)
    ]
    human_message = HumanMessage(content=query)
    input_messages: List[BaseMessage] = [*removals, human_message]
    input_state = InputState(messages=input_messages)

    async for chunk, metadata in graph.astream(
        input=input_state,
        stream_mode="messages",
        config=thread,
    ):
        text = _stringify_content(chunk.content)
        if text and "research_plan" not in metadata.get("tags", []):
            print(text, end="", flush=True)

    latest_snapshot = graph.get_state(thread)
    pending_tasks = latest_snapshot.tasks
    if pending_tasks and len(pending_tasks[0].interrupts) > 0:
        response = input('\n响应可能包含不确定信息。重试生成？如果是，按"y"：')
        if response.lower() == 'y':
            async for chunk, metadata in graph.astream(
                Command(resume=response),
                stream_mode="messages",
                config=thread,
            ):
                if chunk.additional_kwargs.get("tool_calls"):
                    print(chunk.additional_kwargs.get("tool_calls")[0]["function"].get("arguments"), end="")
                if chunk.content:
                    time.sleep(0.05)
                    print(chunk.content, end="", flush=True)


async def main() -> None:
    input_func = builtins.input
    while True:
        query = input_func("> ")
        if query.strip().lower() == "q":
            print("Exiting...")
            break
        await process_query(query)


if __name__ == "__main__":
    asyncio.run(main())

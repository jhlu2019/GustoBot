from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from app.agents.kg_sub_graph.kg_states import CypherOutputState

from langchain_core.prompts import ChatPromptTemplate


planner_system = """
你必须分析输入问题并将其分解为单独的子任务。
如果存在适当的独立任务，则将其作为列表提供，否则返回空列表。
任务不应该相互依赖。
返回要完成的任务列表。
"""


def create_planner_prompt_template() -> ChatPromptTemplate:
    """
    Create a planner prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    message = """Rules:
* Ensure that the tasks are not returning duplicated or similar information.
* Ensure that tasls are NOT dependent on information gathered from other tasks!
* tasks that are dependent on each other should be combined into a single question.
* tasks that return the same information should be combined into a single question.

question: {question}
"""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                planner_system,
            ),
            (
                "human",
                (message),
            ),
        ]
    )

planner_prompt = create_planner_prompt_template()


class CypherHistoryRecord(TypedDict):
    """A simplified representation of the CypherOutputState"""

    task: str
    statement: str
    records: List[Dict[str, Any]]


class HistoryRecord(TypedDict):
    """Information that may be relevant to future user questions."""

    question: str
    answer: str
    cyphers: List[CypherHistoryRecord]


def update_history(
    history: List[HistoryRecord], new: List[HistoryRecord]
) -> List[HistoryRecord]:
    """
    Update the history record. Allow only a max number of records to be stored at any time.

    Parameters
    ----------
    history : List[HistoryRecord]
        The current history list.
    new : List[HistoryRecord]
        The new record to add. Should be a single entry list.

    Returns
    -------
    List[HistoryRecord]
        A new List with the record added and old records removed to maintain size.
    """

    SIZE: int = 5

    history.extend(new)
    return history[-SIZE:]

class InputState(TypedDict):
    """The input state for multi agent workflows."""

    question: str
    data: List[Dict[str, Any]]
    history: Annotated[List[HistoryRecord], update_history]


def create_planner_node(
    llm: BaseChatModel, ignore_node: bool = False, next_action: str = "tool_selection"
) -> Callable[[InputState], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Create a planner node to be used in a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM used to process data.
    ignore_node : bool, optional
        Whether to ignore this node in the workflow, by default False

    Returns
    -------
    Callable[[InputState], OverallState]
        The LangGraph node.
    """

    planner_chain: Runnable[Dict[str, Any], Any] = (
        planner_prompt | llm.with_structured_output(PlannerOutput)
    )


    async def planner(state: InputState) -> Dict[str, Any]:
        """
        Break user query into chunks, if appropriate.
        """
        print("我现在要开始任务分解了！！！")
        if not ignore_node:
            print("我进入的是实际执行！！！！")
            planner_output: PlannerOutput = await planner_chain.ainvoke(
                {"question": state.get("question", "")}
            )
            print(f"planner_output: {planner_output}")
        else:
            print("我进入的是 空列表")
            planner_output = PlannerOutput(tasks=[])
            print(f"planner_output: {planner_output}")
        print("我执行完了！！！")
    
        return {
            "next_action": next_action,
            "tasks": planner_output.tasks
            or [
                Task(
                    question=state.get("question", ""),
                    parent_task=state.get("question", ""),
                )
            ],
            "steps": ["planner"],
        }

    return planner


class Task(BaseModel):
    question: str = Field(..., description="The question to be addressed.")
    parent_task: str = Field(
        ..., description="The parent task this task is derived from."
    )
    requires_visualization: bool = Field(
        default=False,
        description="Whether this task requires a visual to be returned.",
    )
    data: Optional[CypherOutputState] = Field(
        default=None, description="The Cypher query result details."
    )


class PlannerOutput(BaseModel):
    tasks: List[Task] = Field(
        default=[],
        description="A list of tasks that must be complete to satisfy the input question.",
    )






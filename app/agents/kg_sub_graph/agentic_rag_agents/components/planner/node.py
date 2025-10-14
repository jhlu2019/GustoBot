from typing import Any, Callable, Coroutine, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from app.core.logger import get_logger

# 获取日志记录器
logger = get_logger(service="planner_node")

from app.agents.kg_sub_graph.agentic_rag_agents.components.models import Task
from app.agents.kg_sub_graph.agentic_rag_agents.components.planner.models import PlannerOutput
from app.agents.kg_sub_graph.agentic_rag_agents.components.planner.prompts import create_planner_prompt_template
from app.agents.kg_sub_graph.agentic_rag_agents.components.state import InputState


# 定义planner prompt
planner_prompt = create_planner_prompt_template()

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

    # 创建planner chain
    planner_chain: Runnable[Dict[str, Any], Any] = (
        planner_prompt | llm.with_structured_output(PlannerOutput)
    )

    async def planner(state: InputState) -> Dict[str, Any]:
        """
        Break user query into chunks, if appropriate.
        """

        if not ignore_node:
            planner_output: PlannerOutput = await planner_chain.ainvoke(
                {"question": state.get("question", "")}
            )
        else:
            planner_output = PlannerOutput(tasks=[])

        planner_task_decomposition = {
            "next_action": next_action,
            "tasks": planner_output.tasks
            or [
                Task(
                    question=state.get("question", ""),
                    parent_task=state.get("question", ""),
                )   
            ]
        }

        # 日志打印格式，分别打印每个任务
        logger.info(f"Total Sub Task: {len(planner_task_decomposition['tasks'])}")
   
        for i, task in enumerate(planner_task_decomposition['tasks']):
            logger.info(f"Sub Task[{i+1}]: {task.question}")
             
        return planner_task_decomposition

    return planner

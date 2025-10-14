from typing import Any, Callable, Coroutine

from ...components.state import OverallState


def create_final_answer_node() -> (
    Callable[[OverallState], Coroutine[Any, Any, dict[str, Any]]]
):
    """
    Create a final_answer node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM do perform processing.

    Returns
    -------
    Callable[[OverallState], OutputState]
        The LangGraph node.
    """

    async def final_answer(state: OverallState) -> dict[str, Any]:
        """
        Construct a final answer.
        """

        answer = state.get("summary", " ")

        history_record = {
            "question": state.get("question", ""),
            "answer": answer,
            "cyphers": [
                {
                    "task": c.task if hasattr(c, "task") else c.get("task", ""),
                    "records": c.records if hasattr(c, "records") else c.get("records", {}),
                }
                for c in state.get("cyphers", list())
            ],
        }

        return {
            "answer": answer,
            "steps": ["final_answer"],
            "history": [history_record],
        }

    return final_answer

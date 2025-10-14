"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from app.agents.kg_sub_graph.agentic_rag_agents.components.state import OverallState
from app.agents.kg_sub_graph.agentic_rag_agents.components.summarize.prompts import create_summarization_prompt_template

generate_summary_prompt = create_summarization_prompt_template()


def create_summarization_node(
    llm: BaseChatModel,
) -> Callable[[OverallState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Summarization node for a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM do perform processing.

    Returns
    -------
    Callable[[OverallState], OutputState]
        The LangGraph node.
    """

    generate_summary = generate_summary_prompt | llm | StrOutputParser()

    async def summarize(state: OverallState) -> Dict[str, Any]:
        """
        Summarize results of the performed Cypher queries.
        """
        results = []
        
        # 使用直接属性访问而不是get方法
        for cypher in state.get("cyphers", list()):
            # 检查是否是字典类型，使用get方法
            if isinstance(cypher, dict) and cypher.get("records") is not None:
                results.append(cypher.get("records"))
            # 检查是否是Pydantic模型，使用直接属性访问
            elif hasattr(cypher, "records") and cypher.records is not None:
                results.append(cypher.records)
                
        if results:
            summary = await generate_summary.ainvoke(
                {
                    "question": state.get("question"),
                    "results": results,
                }
            )

        else:
            summary = "No data to summarize."

        return {"summary": summary, "steps": ["summarize"]}

    return summarize

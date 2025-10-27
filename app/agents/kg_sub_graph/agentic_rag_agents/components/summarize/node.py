"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, List

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
        text2sql_answers: List[str] = []
        results: List[Any] = []

        for cypher in state.get("cyphers", list()):
            records = None
            if isinstance(cypher, dict):
                records = cypher.get("records")
            elif hasattr(cypher, "records"):
                records = getattr(cypher, "records")

            if not records:
                continue

            if isinstance(records, dict):
                answer = records.get("answer")
                if answer:
                    text2sql_answers.append(str(answer))

                rows = records.get("rows")
                if rows:
                    results.append({"rows": rows, "sql": records.get("sql")})

                other_payload = {
                    key: value
                    for key, value in records.items()
                    if key not in {"answer", "rows", "sql", "visualization", "visualization_config"}
                    and value
                }
                if other_payload:
                    results.append(other_payload)
            else:
                results.append(records)

        if text2sql_answers and not results:
            summary = "\n\n".join(text2sql_answers).strip()
            return {"summary": summary or "No data to summarize.", "steps": ["summarize"]}

        if text2sql_answers:
            combined_answers = "\n\n".join(text2sql_answers).strip()
            additional_summary = ""
            if results:
                additional_summary = await generate_summary.ainvoke(
                    {
                        "question": state.get("question"),
                        "results": results,
                    }
                )
            summary_parts = [combined_answers]
            if additional_summary and additional_summary != "No data to summarize.":
                summary_parts.append(additional_summary)
            summary = "\n\n".join(part for part in summary_parts if part).strip()
            return {"summary": summary or "No data to summarize.", "steps": ["summarize"]}

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

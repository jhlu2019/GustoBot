"""
Tool selection node for orchestrating recipe knowledge graph tools.

This node inspects an incoming question, asks the LLM to pick an appropriate tool
(template-based Cypher, text-to-Cypher, or customer-specific tools), and routes
execution accordingly.
"""

from typing import Any, Callable, Coroutine, Dict, List, Literal, Set

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticToolsParser
from langchain_core.runnables.base import Runnable
from langgraph.types import Command, Send
from pydantic import BaseModel

from app.agents.kg_sub_graph.agentic_rag_agents.components.state import (
    ToolSelectionInputState,
)
from app.agents.kg_sub_graph.agentic_rag_agents.components.tool_selection.prompts import (
    create_tool_selection_prompt_template,
)

# Pre-build the prompt template so we can reuse it across calls.
tool_selection_prompt = create_tool_selection_prompt_template()


def create_tool_selection_node(
    llm: BaseChatModel,
    tool_schemas: List[type[BaseModel]],
    default_to_text2cypher: bool = True,
) -> Callable[[ToolSelectionInputState], Coroutine[Any, Any, Command[Any]]]:
    """
    Create the LangGraph node that decides which tool to invoke for a given task.
    """

    tool_selection_chain: Runnable[Dict[str, Any], Any] = (
        tool_selection_prompt
        | llm.bind_tools(tools=tool_schemas)
        | PydanticToolsParser(tools=tool_schemas, first_tool_only=True)
    )

    # Record tool titles for quick membership checks.
    available_tools: Set[str] = {
        schema.model_json_schema().get("title", "") for schema in tool_schemas
    }

    async def tool_selection(
        state: ToolSelectionInputState,
    ) -> Command[Literal["cypher_query", "predefined_cypher", "customer_tools", "text2sql_query"]]:
        """
        Choose the appropriate tool for the given task.
        """

        go_to_text2cypher: Command[
            Literal["cypher_query", "predefined_cypher", "customer_tools", "text2sql_query"]
        ] = Command(
            goto=Send(
                "cypher_query",
                {
                    "task": state.get("question", ""),
                    "query_name": "cypher_query",
                    "query_parameters": {"question": state.get("question", "")},
                    "steps": ["tool_selection"],
                },
            )
        )

        tool_selection_output: BaseModel | None = await tool_selection_chain.ainvoke(
            {"question": state.get("question", "")}
        )

        if tool_selection_output is not None:
            tool_name: str = tool_selection_output.model_json_schema().get("title", "")
            tool_args: Dict[str, Any] = tool_selection_output.model_dump()

            if tool_name == "predefined_cypher":
                return Command(
                    goto=Send(
                        "predefined_cypher",
                        {
                            "task": state.get("question", ""),
                            "query_name": tool_name,
                            "query_parameters": tool_args,
                            "steps": ["tool_selection"],
                        },
                    )
                )
            if tool_name == "cypher_query":
                return go_to_text2cypher
            if tool_name == "text2sql_query":
                return Command(
                    goto=Send(
                        "text2sql_query",
                        {
                            "task": state.get("question", ""),
                            "query_name": tool_name,
                            "query_parameters": tool_args,
                            "steps": ["tool_selection"],
                        },
                    )
                )
            if tool_name and tool_name in available_tools:
                return Command(
                    goto=Send(
                        "customer_tools",
                        {
                            "task": state.get("question", ""),
                            "query_name": tool_name,
                            "query_parameters": tool_args,
                            "steps": ["tool_selection"],
                        },
                    )
                )

        if default_to_text2cypher:
            return go_to_text2cypher

        return Command(
            goto=Send(
                "error_tool_selection",
                {
                    "task": state.get("question", ""),
                    "errors": [
                        f"Unable to assign tool to question: `{state.get('question', '')}`"
                    ],
                    "steps": ["tool_selection"],
                },
            )
        )

    return tool_selection

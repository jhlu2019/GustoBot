from langchain_core.prompts import ChatPromptTemplate
from app.agents.kg_sub_graph.prompts.kg_prompts import TOOL_SELECTION_SYSTEM_PROMPT


def create_tool_selection_prompt_template() -> ChatPromptTemplate:
    """
    Create a tool selection prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    message = "Question: {question}"

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                TOOL_SELECTION_SYSTEM_PROMPT,
            ),
            (
                "human",
                (message),
            ),
        ]
    )

from langchain_core.prompts import ChatPromptTemplate

visualization_system = """
You must decide how to create a data visualization based on the provided question and previously retrieved data.
Your chart must be either a 'line', 'bar' or 'scatter' chart.
"""


def create_chart_details_prompt_template() -> ChatPromptTemplate:
    """
    Create a visualization prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template requiring `question` and `data` inputs.
    """

    message = """Please create a chart based on this question: {question}
Here is the data you have available to create the chart:
{data}
"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                visualization_system,
            ),
            (
                "human",
                (message),
            ),
        ]
    )

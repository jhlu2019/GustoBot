from langchain_core.prompts import ChatPromptTemplate

correct_chart_details_system = """
You must make corrections to the chart details provided to align with the provided data.
These details will be used to generate a chart to visualize the data.
"""


def create_correct_chart_details_prompt_template() -> ChatPromptTemplate:
    """
    Create a correct chart details prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template requiring `question`, `details`, `errors` and `data` inputs.
    """

    message = """Please fix the chart details for this question: {question}

Here are the current details:
{details}

Here are the current detail errors:
{errors}

Here is the data you have available to create the chart:
{data}
"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                correct_chart_details_system,
            ),
            (
                "human",
                (message),
            ),
        ]
    )

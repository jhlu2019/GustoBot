from langchain.prompts import ChatPromptTemplate


def create_validate_final_answer_prompt_template() -> ChatPromptTemplate:
    """
    Create a validate final answer prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant.",
            ),
            (
                "human",
                (
                    """Your task is to ensure that the provided answer satisfies the input question as completely as possible given the underlying database contents.
Use the provided graph schema to check if there is additional information that needs to be retrieved.
Reference the provided data to see what informed the answer.

Input Question: {question}

Answer: {answer}

Graph Schema:
{schema}

Retrieved Data:
{data}

"""
                ),
            ),
        ]
    )

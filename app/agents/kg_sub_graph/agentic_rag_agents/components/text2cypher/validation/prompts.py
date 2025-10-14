"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_validation_prompt_template() -> ChatPromptTemplate:
    """
    Create a Text2Cypher validation prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    validate_cypher_system = """
    You are a Cypher expert reviewing a statement written by a junior developer.
    """

    validate_cypher_user = """You must check the following:
    * Are there any syntax errors in the Cypher statement?
    * Are there any missing or undefined variables in the Cypher statement?
    * Does the Cypher statement include enough information to answer the question?
    * Ensure that all nodes, relationships and properties are present in the provided schema.

    Examples of good errors:
    * Label (:Foo) does not exist, did you mean (:Bar)?
    * Property bar does not exist for label Foo, did you mean baz?
    * Relationship FOO does not exist, did you mean FOO_BAR?

    Schema:
    {schema}

    The question is:
    {question}

    The Cypher statement is:
    {cypher}

    Make sure you don't make any mistakes!"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                validate_cypher_system,
            ),
            (
                "human",
                (validate_cypher_user),
            ),
        ]
    )

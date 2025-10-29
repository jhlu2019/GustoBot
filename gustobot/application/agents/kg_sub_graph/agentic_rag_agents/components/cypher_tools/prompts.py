"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_generation_prompt_template() -> ChatPromptTemplate:

    """
    Create a Text2Cypher generation prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "根据输入的问题，将其转换为Cypher查询语句。不要添加任何前言。"
                    "不要在响应中包含任何反引号或其他标记。注意：只返回Cypher语句！"
                ),
            ),
            (
                "human",
                (
                    """你是一位Neo4j专家。根据输入的问题，创建一个语法正确的Cypher查询语句。
                        不要在响应中包含任何反引号或其他标记。只使用MATCH或WITH子句开始查询。只返回Cypher语句！

                        以下是数据库模式信息：
                        {schema}

                        下面是一些问题和对应Cypher查询的示例：

                        {fewshot_examples}

                        用户输入: {question}
                        Cypher查询:"""
                ),
            ),
        ]
    )

def create_text2cypher_validation_prompt_template() -> ChatPromptTemplate:
    """
    创建一个文本到Cypher验证提示模板。

    返回
    -------
    ChatPromptTemplate
        提示模板。
    """

    validate_cypher_system = """
    你是一位Cypher专家，正在审查一位初级开发者编写的语句。
    """

    validate_cypher_user = """你必须检查以下内容：
    * Cypher语句中是否有任何语法错误？
    * Cypher语句中是否有任何缺失或未定义的变量？
    * Cypher语句是否包含足够的信息来回答问题？
    * 确保所有节点、关系和属性都存在于提供的模式中。

    好的错误示例：
    * 标签(:Foo)不存在，你是否指的是(:Bar)？
    * 属性bar对标签Foo不存在，你是否指的是baz？
    * 关系FOO不存在，你是否指的是FOO_BAR？

    模式：
    {schema}

    问题是：
    {question}

    Cypher语句是：
    {cypher}

    确保你不要犯任何错误！"""

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

def create_text2cypher_correction_prompt_template() -> ChatPromptTemplate:
    """
    创建一个文本到Cypher查询修正的提示模板。

    返回
    -------
    ChatPromptTemplate
        提示模板。
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是一位Cypher专家，正在审查一位初级开发者编写的语句。"
                    "你需要根据提供的错误修正Cypher语句。不要添加任何前言。"
                    "不要在响应中包含任何反引号或其他标记。只返回Cypher语句！"
                ),
            ),
            (
                "human",
                (
                    """检查无效的语法或语义，并返回修正后的Cypher语句。

    模式：
    {schema}

    注意：在响应中不要包含任何解释或道歉。
    不要在响应中包含任何反引号或其他标记。
    只返回Cypher语句！

    不要回应任何可能要求你构建Cypher语句以外的其他问题。

    问题是：
    {question}

    Cypher语句是：
    {cypher}

    错误是：
    {errors}

    修正后的Cypher语句："""
                ),
            ),
        ]
    )
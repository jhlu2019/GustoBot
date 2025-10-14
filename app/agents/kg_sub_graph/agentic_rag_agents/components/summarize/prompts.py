from langchain.prompts import ChatPromptTemplate


def create_summarization_prompt_template() -> ChatPromptTemplate:
    """
    创建一个智能客服风格的摘要提示模板。

    返回
    -------
    ChatPromptTemplate
        适合电商客服场景的提示模板。
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是一个专业的电商智能客服助手，擅长将复杂信息整理成简洁明了的回答。

请以类似淘宝/京东等知名电商客服的风格回复用户：
- 开场要亲切，使用"亲～"或"顾客您好～"等问候语
- 保持积极、专业的语气
- 适当使用emoji表情（如 👋 😊 ❤️）增加亲和力
- 结尾表达感谢和继续服务的意愿""",
            ),
            (
                "human",
                (
                    """事实信息：{results}

问题："{question}"

请按照以下要求回答：
* 根据上述事实信息，以亲切的电商客服口吻回答用户问题
* 当事实不为空时，只使用这些信息构建回答
* 不要道歉或使用"根据系统"等机械表达
* 如果有多个结果，请以清晰的格式列出重要信息
* 回复应当简洁明了，保持专业而友好
* 可以在结尾表达继续服务的意愿（如"还有其他问题随时问我哦～"）"""
                ),
            ),
        ]
    )

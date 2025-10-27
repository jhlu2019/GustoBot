"""
SQL解释智能体
负责解释SQL语句的含义
"""
from typing import Dict, Any

from autogen_core import message_handler, MessageContext, TopicId, type_subscription
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ModelClientStreamingChunkEvent

from app.schemas.text2sql import SqlMessage, SqlExplanationMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.SQL_EXPLAINER.value)
class SqlExplainerAgent(BaseAgent):
    """SQL解释智能体，负责解释SQL语句的含义"""

    def __init__(self, model_client_instance=None, db_type=None):
        """初始化SQL解释智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
        """
        super().__init__(
            agent_id="sql_explainer_agent",
            agent_name=AGENT_NAMES[AgentTypes.SQL_EXPLAINER.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> str:
        """构建提示模板"""
        return """
        你是一名专业的SQL解释专家，你的任务是以准确、易懂的方式向非技术人员解释给定的SQL语句的含义和作用。

        ## 数据库类型
        {db_type}

        ## 数据库结构
        ```sql
        {db_schema}
        ```

        ## 用户问题
        {query}

        ## 输出格式要求
        **必须使用Markdown格式输出**，包括：
        - 使用 `**粗体**` 强调重要概念
        - 使用有序列表 `1.` 或无序列表 `*` 组织内容
        - 使用 `代码块` 标记SQL关键字和字段名
        - 使用适当的标题层级组织内容

        ## 规则

        1.  **使用通俗易懂的语言：** 解释应该避免使用过于专业或技术性的术语。目标是让没有任何编程或数据库知识的人也能理解。
        2.  **准确且全面地解释：** 确保解释的准确性，并覆盖SQL语句的主要功能和逻辑。
        3.  **解释关键子句：** 针对SQL语句中的每个主要子句（例如 `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `ORDER BY`, `JOIN` 等）解释其作用和目的。
        4.  **解释复杂特性：**
            * **聚合函数：** 如果SQL语句中使用了聚合函数（如 `SUM`, `AVG`, `COUNT`, `MAX`, `MIN`），解释这些函数的作用以及它们是如何计算结果的。
            * **表连接：** 如果使用了表连接（如 `JOIN`），解释为什么要进行连接，以及连接是如何根据相关字段将不同表中的数据关联起来的。可以结合数据库结构进行解释。
            * **子查询：** 如果使用了子查询（嵌套查询），解释子查询的目的以及它是如何帮助主查询获取所需数据的。
        5.  **结合数据库结构：** 在解释过程中，可以适当引用提供的数据库表结构，帮助理解表名、字段名的含义以及表之间的关系。例如，解释 `users.name` 时，可以说明 `name` 是 `users` 表中的一个字段，用于存储用户的姓名。
        6.  **保持简洁明了：** 尽量用简短的句子表达清楚意思，避免冗长的描述。
        7.  **直接解释提供的SQL：** 你的解释应该直接针对用户问题 `{query}` 和 `{sql}` 部分提供的具体SQL代码。
        """

    def _prepare_prompt(self, query: str, sql: str, schema_context: Dict[str, Any] = None) -> str:
        """准备提示模板

        Args:
            query: 用户查询
            sql: SQL语句
            schema_context: 可选的表结构信息

        Returns:
            str: 准备好的提示
        """
        # 格式化表结构信息
        db_schema_str = self.format_schema_context(schema_context) if schema_context else self.db_schema

        # 填充模板
        prompt = self._prompt_template.format(db_type=self.db_type, db_schema=db_schema_str, query=query, sql=sql)
        return prompt

    @message_handler
    async def handle_message(self, message: SqlMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，解释SQL语句"""
        try:
            # 准备提示
            system_message = self._prepare_prompt(message.query, message.sql)

            agent = AssistantAgent(
                name="sql_explainer",
                model_client=self.model_client,
                system_message=system_message,
                model_client_stream=True,
            )

            stream = agent.run_stream(task=f"解释以下SQL语句：\n{message.sql}")
            explanation_content = ""

            async for event in stream:
                if isinstance(event, ModelClientStreamingChunkEvent):
                    # 发送流式内容供实时显示
                    await self.send_response(event.content)
                elif isinstance(event, TaskResult):
                    explanation_content = event.messages[-1].content.strip()

            # 发送最终标记，不发送额外内容避免重复
            await self.send_response(
                "\n\nSQL解释完成",
                is_final=True,
            )

            # 构造SqlExplanationMessage并传递给下一个智能体
            explanation_message = SqlExplanationMessage(
                query=message.query,
                sql=message.sql,
                explanation=explanation_content,
                connection_id=getattr(message, 'connection_id', None)
            )

            await self.publish_message(
                explanation_message,
                topic_id=TopicId(type=TopicTypes.SQL_EXECUTOR.value, source=self.id.key)
            )
        except Exception as e:
            await self.handle_exception("handle_message", e)

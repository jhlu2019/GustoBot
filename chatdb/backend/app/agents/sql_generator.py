"""
SQL生成智能体
负责将自然语言转换为SQL
"""
from typing import Dict, Any

from autogen_core import message_handler, MessageContext, TopicId, type_subscription
from autogen_agentchat.agents import AssistantAgent

from app.schemas.text2sql import AnalysisMessage, SqlMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.SQL_GENERATOR.value)
class SqlGeneratorAgent(BaseAgent):
    """SQL生成智能体，负责将自然语言转换为SQL"""

    def __init__(self, model_client_instance=None, db_type=None):
        """初始化SQL生成智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
        """
        super().__init__(
            agent_id="sql_generator_agent",
            agent_name=AGENT_NAMES[AgentTypes.SQL_GENERATOR.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> str:
        """构建提示模板"""
        return """
        你是一名专业的SQL转换专家。你的任务是基于上下文信息及SQL命令生成报告，将用户的自然语言查询转换为精确的SQL语句。

        ## 生成SQL的指导原则：

        1.  **严格遵循报告中的分析：** 仔细阅读并理解上述的SQL命令生成报告，包括查询意图、需要使用的表和字段、连接方式、筛选条件、分组和排序要求。
        2.  **生成有效的SQL语句：** 仅输出符合 {db_type} 数据库语法的有效SQL语句，不要添加任何额外的解释或说明。
        3.  **准确表达筛选条件：** 报告中如有筛选条件描述，务必在生成的SQL语句中准确实现。
        4.  **正确使用表连接：** 按照报告中"需要的表连接描述"进行表连接，并确保连接条件正确。
        5.  **实现分组和聚合：** 如果报告中指示需要进行分组（GROUP BY）或聚合操作（例如 SUM, COUNT, AVG），请在SQL语句中正确实现。
        6.  **实现排序：** 按照报告中"排序描述"的要求，使用 ORDER BY 子句对结果进行排序。
        7.  **考虑数据库特性：** 生成的SQL语句应符合 {db_type} 数据库的特定语法和函数。
        8.  **SQL格式规范：** 使用清晰可读的SQL格式，适当添加换行和缩进，以提高可读性。
        9.  **避免使用不支持的语法：** 不要使用 {db_type} 数据库不支持的特殊语法或函数。
        10. **仅生成SQL：** 最终输出结果必须是纯粹的SQL查询语句，没有任何额外的文本。
        11. **注意值映射：** 如果提供了值映射信息，请根据映射关系在SQL中使用正确的数据库值。
        12. **避免重复字段和语句：** 确保生成的SQL语句中不包含重复的字段名称或重复的SQL子句，如重复的FROM子句。例如，避免生成如 `SELECT field1, field1` 或 `FROM table1 FROM table1` 这样的语句。
        13. **检查语法错误：** 在生成SQL语句后，仔细检查是否有语法错误，如拼写错误、缺失逗号或括号不匹配等。确保生成的SQL语句是完整的，不包含多余的关键字或缺失必要的关键字。

        特别注意：请严格根据上下文提供的 `SQL 命令分析报告` 最终只生成一条您认为最符合用户查询需求的SQL语句。
        """

    def _prepare_prompt(self, schema_context: Dict[str, Any] = None, mappings_str: str = "") -> str:
        """准备提示模板

        Args:
            schema_context: 可选的表结构信息
            mappings_str: 值映射字符串，默认为空字符串

        Returns:
            str: 准备好的提示
        """
        prompt = self._prompt_template.format(db_type=self.db_type)

        # 如果有表结构信息，则添加到提示中
        if schema_context and schema_context.get('tables'):
            prompt += self.format_schema_as_markdown(schema_context)

        return prompt

    @message_handler
    async def handle_analysis_message(self, message: AnalysisMessage, ctx: MessageContext) -> None:
        """处理AnalysisMessage类型的消息"""
        try:
            # 从memory_content重建ListMemory对象
            memory = self.rebuild_memory_from_content(message.memory_content)

            # 准备系统提示
            # mappings_str = message.mappings_str or ""
            # system_message = self._prepare_prompt(message.schema_context, mappings_str)

            system_message = self._prompt_template.format(db_type=self.db_type)

            agent = AssistantAgent(
                name="sql_generator",
                model_client=self.model_client,
                system_message=system_message,
                memory=[memory],
                model_client_stream=True,
            )

            result = await agent.run(task="严格根据上下文信息生成SQL语句")
            sql_content = result.messages[-1].content

            # 首先将SQL内容发送为流式消息，供前端实时更新
            # await self.send_response(sql_content)

            # 发送SQL内容为final_sql类型，触发前端SQL语句区域显示
            await self.send_response(
                "SQL语句已生成",
                is_final=True,
                result={"sql": sql_content}  # 使用正确的格式包含SQL语句
            )

            # 构造SqlMessage并传递给下一个智能体
            sql_message = SqlMessage(
                query=message.query,
                sql=sql_content,
                connection_id=getattr(message, 'connection_id', None)
            )

            await self.publish_message(
                sql_message,
                topic_id=TopicId(type=TopicTypes.SQL_EXPLAINER.value, source=self.id.key)
            )
        except Exception as e:
            await self.handle_exception("handle_analysis_message", e)

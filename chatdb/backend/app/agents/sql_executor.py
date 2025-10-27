"""
SQL执行智能体
负责执行SQL并返回结果
"""
from typing import Optional

from autogen_core import message_handler, MessageContext, TopicId, type_subscription

from app.db.dbaccess import DBAccess
from app.schemas.text2sql import SqlExplanationMessage, SqlResultMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.SQL_EXECUTOR.value)
class SqlExecutorAgent(BaseAgent):
    """SQL执行智能体，负责执行SQL并返回结果"""

    def __init__(self, model_client_instance=None, db_type=None, db_access: Optional[DBAccess] = None):
        """初始化SQL执行智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
            db_access: 数据库访问对象，如果为None则使用全局dbAccess
        """
        super().__init__(
            agent_id="sql_executor_agent",
            agent_name=AGENT_NAMES[AgentTypes.SQL_EXECUTOR.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )
        self.db_access = db_access

    def _clean_sql(self, sql: str) -> str:
        """清理SQL语句，移除可能的标记

        Args:
            sql: 原始SQL语句

        Returns:
            str: 清理后的SQL语句
        """
        return sql.replace("```sql", "").replace("```", "").strip()

    async def _execute_sql(self, sql: str, connection_id: Optional[int] = None) -> tuple[list, Optional[str]]:
        """执行SQL查询

        Args:
            sql: SQL语句
            connection_id: 连接ID

        Returns:
            tuple[list, Optional[str]]: (结果列表, 错误信息)
        """
        try:
            # 清理SQL语句
            cleaned_sql = self._clean_sql(sql)

            # 执行SQL查询
            results = self.db_access.run_sql(cleaned_sql)

            # 检查结果
            if results is None or len(results) == 0:
                return [], None
            else:
                # 转换为字典列表
                return results.to_dict("records"), None

        except Exception as e:
            error_msg = f"SQL执行错误: {str(e)}"
            return [], error_msg

    @message_handler
    async def handle_message(self, message: SqlExplanationMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，执行SQL查询"""
        try:
            # await self.send_response("正在执行SQL查询...")

            # 使用已创建的数据库访问对象
            connection_id = getattr(message, 'connection_id', None)
            # if connection_id is not None:
            #     await self.send_response(f"使用连接ID: {connection_id}")
            # else:
            #     await self.send_response("未提供连接ID，使用默认连接")

            # 执行SQL查询
            results, error_msg = await self._execute_sql(message.sql, connection_id)

            if error_msg:
                # 处理数据库查询错误
                await self.send_error(error_msg)

                # 尽管有错误，仍然尝试发送空结果给下一个智能体
                await self.publish_message(
                    SqlResultMessage(
                        query=message.query,
                        sql=message.sql,
                        explanation=message.explanation,
                        results=[],  # 空结果
                        connection_id=connection_id,
                    ),
                    topic_id=TopicId(type=TopicTypes.VISUALIZATION_RECOMMENDER.value, source=self.id.key)
                )
            else:
                # 成功执行
                if len(results) == 0:
                    await self.send_response("查询执行成功，但没有返回任何结果\n\n")
                else:
                    await self.send_response(f"SQL执行完成，获取到{len(results)}条结果\n\n")

                # 发送结果数据到data区域
                await self.send_response(
                    f"查询执行完成，返回{len(results)}条数据",
                    is_final=True,
                    result={"results": results}
                )

                # 构造SqlResultMessage并传递给下一个智能体
                result_message = SqlResultMessage(
                    query=message.query,
                    sql=message.sql,
                    explanation=message.explanation,
                    results=results,
                    connection_id=connection_id
                )

                await self.publish_message(
                    result_message,
                    topic_id=TopicId(type=TopicTypes.VISUALIZATION_RECOMMENDER.value, source=self.id.key)
                )

        except Exception as e:
            await self.handle_exception("handle_message", e)

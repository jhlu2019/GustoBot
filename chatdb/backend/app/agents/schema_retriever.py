"""
表结构检索智能体
负责从图数据库获取相关表结构
"""
from typing import Dict, Any, Tuple

from autogen_core import message_handler, MessageContext, TopicId, type_subscription

from app.db.session import SessionLocal
from app.services.text2sql_service import retrieve_relevant_schema, get_value_mappings
from app.schemas.text2sql import QueryMessage, SchemaContextMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.SCHEMA_RETRIEVER.value)
class SchemaRetrieverAgent(BaseAgent):
    """表结构检索智能体，负责从图数据库获取相关表结构"""

    def __init__(self, model_client_instance=None, db_type=None):
        """初始化表结构检索智能体"""
        super().__init__(
            agent_id="schema_retriever_agent",
            agent_name=AGENT_NAMES[AgentTypes.SCHEMA_RETRIEVER.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )

    async def retrieve_schema(self, connection_id: int, query: str) -> Tuple[Dict[str, Any], str]:
        """从图数据库获取相关表结构信息

        Args:
            connection_id: 数据库连接ID
            query: 用户查询

        Returns:
            Tuple[Dict[str, Any], str]: 表结构信息字典和值映射字符串
        """
        schema_context = {}
        mappings_str = ""
        try:
            # 创建数据库会话
            db = SessionLocal()
            try:
                # 调用 retrieve_relevant_schema 方法获取相关表结构
                schema_context = await retrieve_relevant_schema(db=db, connection_id=connection_id, query=query)
                value_mappings = get_value_mappings(db, schema_context)
                if value_mappings:
                    mappings_str = "-- Value Mappings:\n"
                    for column, mappings in value_mappings.items():
                        mappings_str += f"-- For {column}:\n"
                        for nl_term, db_value in mappings.items():
                            mappings_str += f"--   '{nl_term}' in natural language refers to '{db_value}' in the database\n"
                    mappings_str += "\n"
            finally:
                db.close()
        except Exception as e:
            await self.handle_exception("retrieve_schema", e)

        return schema_context, mappings_str

    @message_handler
    async def handle_message(self, message: QueryMessage, ctx: MessageContext) -> None:
        """处理查询消息，从图数据库获取相关表结构信息

        Args:
            message: 查询消息
            ctx: 消息上下文
        """
        try:
            connection_id = None
            schema_context = {}

            # 发送开始处理的消息
            await self.send_response("正在从图数据库解析相关表结构...\n\n")

            mappings_str = ""
            if message.connection_id:
                connection_id = message.connection_id
                print(f"[{self.agent_name}] 收到连接ID: {connection_id}")

                # 从图数据库获取相关表结构信息和值映射
                schema_context, mappings_str = await self.retrieve_schema(connection_id, message.query)

                # 输出找到的相关表信息
                if schema_context and schema_context.get('tables'):
                    tables_info = "\n".join([f"- {table['name']}" for table in schema_context['tables']])
                    await self.send_response(f"已找到以下相关表:\n{tables_info} \n\n")
                else:
                    await self.send_response("未找到相关表结构，将使用默认数据库结构继续分析\n\n")
            else:
                await self.send_response("未提供数据库连接ID，将使用默认数据库结构继续分析\n\n")

            # 发送完成消息
            await self.send_response("表结构检索完成\n\n", is_final=True)

            # 将表结构信息和值映射传递给查询分析智能体
            await self.publish_message(
                SchemaContextMessage(
                    query=message.query,
                    connection_id=connection_id,
                    schema_context=schema_context,
                    mappings_str=mappings_str
                ),
                topic_id=TopicId(type=TopicTypes.QUERY_ANALYZER.value, source=self.id.key)
            )
        except Exception as e:
            await self.handle_exception("handle_message", e)

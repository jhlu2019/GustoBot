# """
# 智能体服务 - 已废弃
# 此文件已被重构，请使用新的架构：
# - app.services.agent_orchestrator.AgentOrchestrator
# - app.agents 模块中的各个智能体
#
# 此文件仅保留用于向后兼容，建议迁移到新架构。
# """
#
# # 废弃警告
# import warnings
# warnings.warn(
#     "agent_service.py 已废弃，请使用 app.services.agent_orchestrator.AgentOrchestrator 和 app.agents 模块",
#     DeprecationWarning,
#     stacklevel=2
# )
#
# from typing import Optional
#
# # 向后兼容的导入
# from app.agents.base import StreamResponseCollector, BaseAgent
# from app.services.agent_orchestrator import AgentOrchestrator
# from app.agents.types import TOPIC_TYPES as topic_types_dict
# from app.agents.types import AGENT_NAMES, DEFAULT_DB_TYPE as DB_TYPE
#
# # 向后兼容的主题类型常量
# sql_generator_topic_type = topic_types_dict["sql_generator"]
# sql_explainer_topic_type = topic_types_dict["sql_explainer"]
# sql_executor_topic_type = topic_types_dict["sql_executor"]
# visualization_recommender_topic_type = topic_types_dict["visualization_recommender"]
# stream_output_topic_type = topic_types_dict["stream_output"]
# query_analyzer_topic_type = topic_types_dict["query_analyzer"]
# schema_retriever_topic_type = topic_types_dict["schema_retriever"]
#
#
# class Text2SQLService:
#     """Text2SQL服务类 - 已废弃
#
#     此类已废弃，请使用 AgentOrchestrator 替代。
#     保留此类仅为向后兼容。
#     """
#
#     def __init__(self):
#         """初始化Text2SQL服务"""
#         warnings.warn(
#             "Text2SQLService 已废弃，请使用 AgentOrchestrator",
#             DeprecationWarning,
#             stacklevel=2
#         )
#         self.orchestrator = AgentOrchestrator()
#
#     async def process_query(self, query: str, collector: StreamResponseCollector = None,
#                           connection_id: Optional[int] = None):
#         """处理自然语言查询，返回SQL和结果
#
#         Args:
#             query: 自然语言查询
#             collector: 流式响应收集器
#             connection_id: 数据库连接ID，可选
#         """
#         return await self.orchestrator.process_query(query, collector, connection_id)

"""
智能体工厂
统一创建和注册智能体
"""
from typing import Dict, Any, Callable, Optional

from autogen_core import SingleThreadedAgentRuntime, ClosureAgent, TypeSubscription

from app.core.config import settings
from app.core.llms import model_client
from app.db.dbaccess import DBAccess
from .base import StreamResponseCollector
from .types import AgentTypes, TopicTypes
from .schema_retriever import SchemaRetrieverAgent
from .query_analyzer import QueryAnalyzerAgent
from .sql_generator import SqlGeneratorAgent
from .sql_explainer import SqlExplainerAgent
from .sql_executor import SqlExecutorAgent
from .visualization_recommender import VisualizationRecommenderAgent


class AgentFactory:
    """智能体工厂，负责创建和注册所有智能体"""

    def __init__(self, db_type: str = None, db_access: Optional[DBAccess] = None):
        """初始化智能体工厂

        Args:
            db_type: 数据库类型
            db_access: 数据库访问对象
        """
        self.db_type = db_type
        self.db_access = db_access

    async def register_all_agents(self, runtime: SingleThreadedAgentRuntime,
                                collector: StreamResponseCollector, user_feedback_enabled: bool = False) -> None:
        """注册所有智能体到运行时

        Args:
            runtime: 单线程智能体运行时
            collector: 流式响应收集器
            user_feedback_enabled: 是否启用用户反馈功能
        """
        # 注册表结构检索智能体
        await self._register_schema_retriever(runtime)

        # 注册查询分析智能体
        await self._register_query_analyzer(runtime, collector, user_feedback_enabled)

        # 注册SQL生成智能体（根据配置选择）
        await self._register_sql_generator(runtime)

        # 注册SQL解释智能体
        await self._register_sql_explainer(runtime)

        # 注册SQL执行智能体
        await self._register_sql_executor(runtime)

        # 注册可视化推荐智能体
        await self._register_visualization_recommender(runtime)

        # 注册消息收集器
        await self._register_stream_collector(runtime, collector)

    async def _register_schema_retriever(self, runtime: SingleThreadedAgentRuntime) -> None:
        """注册表结构检索智能体"""
        await SchemaRetrieverAgent.register(
            runtime,
            TopicTypes.SCHEMA_RETRIEVER.value,
            lambda: SchemaRetrieverAgent(
                model_client_instance=model_client,
                db_type=self.db_type
            )
        )

    async def _register_query_analyzer(self, runtime: SingleThreadedAgentRuntime,
                                     collector: StreamResponseCollector, user_feedback_enabled: bool = False) -> None:
        """注册查询分析智能体"""
        await QueryAnalyzerAgent.register(
            runtime,
            TopicTypes.QUERY_ANALYZER.value,
            lambda: QueryAnalyzerAgent(
                model_client_instance=model_client,
                db_type=self.db_type,
                input_func=collector.user_input if user_feedback_enabled else None
            )
        )

    async def _register_sql_generator(self, runtime: SingleThreadedAgentRuntime) -> None:
        """注册SQL生成智能体（根据配置选择）"""
        if settings.HYBRID_RETRIEVAL_ENABLED:
            # 使用混合检索增强的SQL生成智能体
            from .hybrid_sql_generator import HybridSqlGeneratorAgent
            await HybridSqlGeneratorAgent.register(
                runtime,
                TopicTypes.SQL_GENERATOR.value,
                lambda: HybridSqlGeneratorAgent(
                    model_client_instance=model_client,
                    db_type=self.db_type
                )
            )
        else:
            # 使用原始的SQL生成智能体
            await SqlGeneratorAgent.register(
                runtime,
                TopicTypes.SQL_GENERATOR.value,
                lambda: SqlGeneratorAgent(
                    model_client_instance=model_client,
                    db_type=self.db_type
                )
            )

    async def _register_sql_explainer(self, runtime: SingleThreadedAgentRuntime) -> None:
        """注册SQL解释智能体"""
        await SqlExplainerAgent.register(
            runtime,
            TopicTypes.SQL_EXPLAINER.value,
            lambda: SqlExplainerAgent(
                model_client_instance=model_client,
                db_type=self.db_type
            )
        )

    async def _register_sql_executor(self, runtime: SingleThreadedAgentRuntime) -> None:
        """注册SQL执行智能体"""
        await SqlExecutorAgent.register(
            runtime,
            TopicTypes.SQL_EXECUTOR.value,
            lambda: SqlExecutorAgent(
                model_client_instance=model_client,
                db_type=self.db_type,
                db_access=self.db_access
            )
        )

    async def _register_visualization_recommender(self, runtime: SingleThreadedAgentRuntime) -> None:
        """注册可视化推荐智能体"""
        await VisualizationRecommenderAgent.register(
            runtime,
            TopicTypes.VISUALIZATION_RECOMMENDER.value,
            lambda: VisualizationRecommenderAgent(
                model_client_instance=model_client,
                db_type=self.db_type
            )
        )

    async def _register_stream_collector(self, runtime: SingleThreadedAgentRuntime,
                                       collector: StreamResponseCollector) -> None:
        """注册消息收集器"""
        await ClosureAgent.register_closure(
            runtime,
            "stream_collector_agent",
            collector.callback,
            subscriptions=lambda: [
                TypeSubscription(
                    topic_type=TopicTypes.STREAM_OUTPUT.value,
                    agent_type="stream_collector_agent"
                )
            ],
        )

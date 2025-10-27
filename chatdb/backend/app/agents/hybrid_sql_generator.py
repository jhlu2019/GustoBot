"""
混合SQL生成智能体
集成Neo4j+Milvus双引擎检索的增强版SQL生成智能体
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from autogen_core import message_handler, MessageContext, TopicId, type_subscription
from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

from app.core.config import settings
from app.schemas.text2sql import AnalysisMessage, SqlMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes

logger = logging.getLogger(__name__)


@type_subscription(topic_type=TopicTypes.SQL_GENERATOR.value)
class HybridSqlGeneratorAgent(BaseAgent):
    """混合SQL生成智能体，集成Neo4j+Milvus双引擎检索"""

    def __init__(self, model_client_instance=None, db_type=None):
        """初始化混合SQL生成智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
        """
        super().__init__(
            agent_id="hybrid_sql_generator_agent",
            agent_name=AGENT_NAMES[AgentTypes.SQL_GENERATOR.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )

        # 初始化混合检索引擎
        self.hybrid_engine = None
        self._initialized = False

        # 构建基础提示模板
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
        # if schema_context and schema_context.get('tables'):
        #     prompt += self.format_schema_as_markdown(schema_context)

        return prompt

    async def _ensure_initialized(self):
        """确保混合检索引擎已初始化"""
        if not self._initialized and settings.HYBRID_RETRIEVAL_ENABLED:
            try:
                # 延迟导入避免循环依赖
                from app.services.hybrid_retrieval_service import HybridRetrievalEngine
                self.hybrid_engine = HybridRetrievalEngine()
                await self.hybrid_engine.initialize()
                self._initialized = True
                await self.send_response("混合检索引擎初始化成功\n\n")
            except Exception as e:
                await self.send_response(f"混合检索引擎初始化失败: {str(e)}")
                self._initialized = False

    @message_handler
    async def handle_analysis_message(self, message: AnalysisMessage, ctx: MessageContext) -> None:
        """处理AnalysisMessage类型的消息，使用混合检索生成SQL"""
        try:
            # 确保服务已初始化
            await self._ensure_initialized()

            # 从memory_content重建ListMemory对象
            memory = self.rebuild_memory_from_content(message.memory_content)

            # 获取消息内容
            query = message.query
            schema_context = message.schema_context
            connection_id = getattr(message, 'connection_id', None)
            mappings_str = message.mappings_str or ""

            # # 如果有表结构信息，通知用户
            # if schema_context and schema_context.get('tables'):
            #     await self.send_response("正在使用从图数据库获取的相关表结构生成SQL...")
            #
            # # 如果有值映射信息，通知用户
            # if mappings_str:
            #     await self.send_response("已加载值映射信息，将在SQL生成中使用...")

            await self.send_response("正在使用混合检索引擎查找相关示例...\n\n")

            # 使用混合检索引擎
            similar_examples = []

            if self._initialized and settings.HYBRID_RETRIEVAL_ENABLED:
                try:
                    similar_examples = await self.hybrid_engine.hybrid_retrieve(
                        query=query,
                        schema_context=schema_context,
                        connection_id=connection_id or 0,
                        top_k=settings.MAX_EXAMPLES_PER_QUERY
                    )

                    if similar_examples:
                        # await self.send_response(
                        #     f"找到 {len(similar_examples)} 个高质量相关示例，正在生成优化SQL..."
                        # )
                        system_message = self._build_enhanced_prompt_with_examples(
                            query, schema_context, similar_examples, mappings_str
                        )
                    else:
                        # await self.send_response("未找到相关示例，使用标准模式生成SQL...")
                        system_message = self._prepare_prompt(schema_context, mappings_str)

                except Exception as e:
                    await self.send_response(f"检索示例时出错，使用标准模式: {str(e)} \n\n")
                    system_message = self._prepare_prompt(schema_context, mappings_str)
            else:
                system_message = self._prepare_prompt(schema_context, mappings_str)

            # 生成SQL
            agent = AssistantAgent(
                name="hybrid_sql_generator",
                model_client=self.model_client,
                system_message=system_message,
                memory=[memory],
                model_client_stream=True,
            )

            result = await agent.run(task="严格根据上下文信息生成SQL语句")
            sql_content = result.messages[-1].content

            # 首先将SQL内容发送为流式消息，供前端实时更新
            await self.send_response(sql_content)

            # 学习新的问答对
            if self._initialized and settings.AUTO_LEARNING_ENABLED and self._is_valid_sql(sql_content):
                await self._learn_qa_pair(query, sql_content, schema_context, connection_id)

            # 发送SQL内容为final_sql类型，触发前端SQL语句区域显示
            await self.send_response(
                "SQL语句已生成",
                is_final=True,
                result={"sql": sql_content, "examples_used": len(similar_examples)}
            )

            # 构造SqlMessage并传递给下一个智能体
            sql_message = SqlMessage(
                query=query,
                sql=sql_content,
                connection_id=connection_id
            )

            await self.publish_message(
                sql_message,
                topic_id=TopicId(type=TopicTypes.SQL_EXPLAINER.value, source=self.id.key)
            )

        except Exception as e:
            await self.handle_exception("handle_analysis_message", e)

    def _build_enhanced_prompt_with_examples(self, query: str, schema_context: Dict,
                                           examples: List, mappings_str: str) -> str:
        """构建包含示例的增强提示"""
        examples_text = self._format_examples(examples)

        # 使用基础提示模板并添加示例
        base_prompt = self._prepare_prompt(schema_context, mappings_str)

        enhanced_prompt = f"""
{base_prompt}

## 相关示例参考

{examples_text}

## 生成指导原则
0. **严格根据上下文信息**：确保生成的SQL语句能够准确回答用户的问题
1. **参考示例模式**：学习示例中的查询模式和结构
2. **确保语法正确**：生成可执行的标准SQL语句
3. **优化性能**：使用高效的查询方式
4. **考虑最佳实践**：遵循示例中展示的最佳实践

特别注意：请严格根据以上信息及上下文提供的 `SQL 命令分析报告` 最终只生成一条您认为最符合用户查询需求的SQL语句。
"""
        return enhanced_prompt

    def _format_examples(self, examples: List) -> str:
        """格式化示例"""
        if not examples:
            return "暂无相关示例"

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            formatted_examples.append(f"""
### 示例 {i} (相关度: {getattr(example, 'final_score', 0.0):.2f})
**问题**: {getattr(example.qa_pair, 'question', '')}
**SQL**:
```sql
{getattr(example.qa_pair, 'sql', '')}
```
**推荐理由**: {getattr(example, 'explanation', '')}
**查询类型**: {getattr(example.qa_pair, 'query_type', '')}
**难度等级**: {getattr(example.qa_pair, 'difficulty_level', 1)}
""")

        return "\n".join(formatted_examples)

    def _is_valid_sql(self, sql_content: str) -> bool:
        """简单验证SQL是否有效"""
        if not sql_content:
            return False

        # 提取SQL语句
        sql = self._extract_sql_from_content(sql_content)

        # 基本验证
        sql_lower = sql.lower().strip()
        return (sql_lower.startswith('select') or
                sql_lower.startswith('with') or
                sql_lower.startswith('(select'))

    def _extract_sql_from_content(self, content: str) -> str:
        """从内容中提取SQL语句"""
        import re

        # 查找SQL代码块
        sql_match = re.search(r'```sql\n(.*?)\n```', content, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()

        # 查找任何代码块
        code_match = re.search(r'```(.*?)```', content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # 如果没有代码块，返回原内容
        return content.strip()

    async def _learn_qa_pair(self, question: str, sql: str,
                           schema_context: Dict, connection_id: int):
        """学习新的问答对"""
        try:
            if not self.hybrid_engine:
                return

            # 延迟导入避免循环依赖
            from app.services.hybrid_retrieval_service import (
                QAPairWithContext, extract_tables_from_sql,
                extract_entities_from_question, clean_sql, generate_qa_id
            )

            # 提取SQL中使用的表
            used_tables = extract_tables_from_sql(sql)

            # 分析查询类型和难度
            query_type = self._classify_query_type(question)
            difficulty = self._estimate_difficulty(sql)

            # 提取实体
            entities = extract_entities_from_question(question)

            # 创建问答对对象
            qa_pair = QAPairWithContext(
                id=generate_qa_id(),
                question=question,
                sql=clean_sql(sql),
                connection_id=connection_id or 0,
                difficulty_level=difficulty,
                query_type=query_type,
                success_rate=0.0,
                verified=False,
                created_at=datetime.now(),
                used_tables=used_tables,
                used_columns=[],
                query_pattern=query_type,
                mentioned_entities=entities
            )

            # 异步存储（不阻塞主流程）
            await self.hybrid_engine.store_qa_pair(qa_pair, schema_context)
            await self.send_response("已学习当前问答对，将用于未来的智能推荐")

        except Exception as e:
            # 学习失败不应该影响主流程
            logger.error(f"学习问答对时出错: {str(e)}")

    def _classify_query_type(self, question: str) -> str:
        """分类查询类型"""
        question_lower = question.lower()

        if any(word in question_lower for word in ['count', 'sum', 'avg', 'max', 'min', '统计', '计算', '总数']):
            return "AGGREGATE"
        elif any(word in question_lower for word in ['join', '连接', '关联', '联合']):
            return "JOIN"
        elif any(word in question_lower for word in ['group', '分组', '按照', '分类']):
            return "GROUP_BY"
        elif any(word in question_lower for word in ['order', '排序', '排列']):
            return "ORDER_BY"
        else:
            return "SELECT"

    def _estimate_difficulty(self, sql: str) -> int:
        """估算SQL难度等级"""
        sql_lower = sql.lower()

        difficulty = 1

        # 检查复杂性指标
        if 'join' in sql_lower:
            difficulty += 1
        if 'group by' in sql_lower:
            difficulty += 1
        if 'having' in sql_lower:
            difficulty += 1
        if any(word in sql_lower for word in ['subquery', '子查询']) or '(' in sql:
            difficulty += 1
        if 'union' in sql_lower:
            difficulty += 1

        return min(5, difficulty)

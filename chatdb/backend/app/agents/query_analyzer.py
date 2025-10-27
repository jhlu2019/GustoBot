"""
查询分析智能体
负责分析用户查询和表结构的关系
"""
from typing import Dict, Any, Optional, Callable, Awaitable

from autogen_core import message_handler, MessageContext, TopicId, type_subscription, CancellationToken
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage, UserInputRequestedEvent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

from app.schemas.text2sql import SchemaContextMessage, AnalysisMessage
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.QUERY_ANALYZER.value)
class QueryAnalyzerAgent(BaseAgent):
    """查询分析智能体，负责分析用户查询和表结构的关系"""

    def __init__(self, model_client_instance=None, db_type=None, input_func=None):
        """初始化查询分析智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
            input_func: 用户输入函数
        """
        super().__init__(
            agent_id="query_analyzer_agent",
            agent_name=AGENT_NAMES[AgentTypes.QUERY_ANALYZER.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )
        # 用户输入函数，用于交互式分析
        self.input_func = input_func
        self._system_message = self._build_system_message()
        self._task_template = self._build_task_template()

    def _build_system_message(self) -> str:
        """构建系统消息 - 定义角色和能力"""
        return """你是一名专业的数据库查询分析专家，具备以下核心能力：

**角色定位：**
- 深度理解自然语言查询意图
- 精确分析数据库表结构关系
- 生成结构化的SQL分析报告

**分析方法：**
1. **意图识别**：准确理解用户查询的核心目标和业务需求
2. **实体映射**：将自然语言概念映射到数据库表和字段
3. **关系分析**：识别表间关系和必要的连接操作
4. **条件提取**：从查询中提取筛选、分组、排序等条件
5. **结构设计**：构思合理的SQL查询结构框架

**输出要求：**
- 使用Markdown格式，结构清晰
- 分析详尽但重点突出
- 为后续SQL生成提供准确指导
- 识别潜在歧义并提出解决方案

**交互原则：**
- 如果用户提出修改建议，只输出修改部分，不重复整个报告
- 保持专业性和准确性
- 确保分析结果可操作性强"""

    def _build_task_template(self) -> str:
        """构建任务模板 - 具体的分析任务"""
        return """请基于以下信息生成SQL命令分析报告：
**数据库环境：**
- 数据库类型：{db_type}
- 数据库结构：
```sql
{db_schema}
```

**值映射信息：**
```
{mappings_str}
```

**用户查询：**
{query}

**请按以下markdown格式输出详细的分析报告：**

## SQL 命令分析报告

### 1. 查询意图分析
[详细描述用户查询的核心意图和业务目标]

### 2. 涉及的数据实体
**主要表：**
- [表名1] - [用途说明]
- [表名2] - [用途说明]

**关键字段：**
- 表名1: [字段1], [字段2] - [用途说明]
- 表名2: [字段1], [字段2] - [用途说明]

### 3. 表关系与连接
[描述需要的表连接关系和连接条件]

### 4. 查询条件分析
**筛选条件：**
- [条件1] - [说明]
- [条件2] - [说明]

**分组要求：**
[是否需要分组及分组字段]

**排序要求：**
[是否需要排序及排序规则]

### 5. SQL结构框架
```sql
-- 基于分析的SQL查询结构
SELECT [字段列表]
FROM [主表]
[连接语句]
WHERE [筛选条件]
[GROUP BY 分组]
[ORDER BY 排序]
[LIMIT 限制]
```

### 6. 潜在问题与建议
[识别查询中的歧义或需要澄清的地方]
"""

    def _prepare_task(self, query: str, schema_context: Dict[str, Any], mappings_str: str = "") -> str:
        """准备具体的分析任务

        Args:
            query: 用户查询
            schema_context: 表结构信息
            mappings_str: 值映射字符串，默认为空字符串

        Returns:
            str: 准备好的任务描述
        """
        # 格式化表结构信息
        db_schema_str = self.format_schema_context(schema_context)

        # 处理值映射信息
        mappings_display = mappings_str if mappings_str.strip() else "无特殊值映射"

        # 填充任务模板
        task = self._task_template.format(
            query=query,
            db_type=self.db_type,
            db_schema=db_schema_str,
            mappings_str=mappings_display
        )
        return task


    @message_handler
    async def handle_message(self, message: SchemaContextMessage, ctx: MessageContext) -> None:
        """处理接收到的表结构信息消息，分析查询意图和所需表结构"""
        try:
            # 获取连接ID、表结构信息和值映射
            connection_id = message.connection_id
            schema_context = message.schema_context
            query = message.query
            mappings_str = message.mappings_str or ""

            # 创建agent并执行任务
            agent = AssistantAgent(
                name="query_analyzer",
                model_client=self.model_client,
                system_message=self._system_message,
                model_client_stream=True,
            )
            memory = ListMemory()
            analysis_content = ""

            # 如果需要用户对分析报告进行反馈
            if self.input_func:
                user_proxy = UserProxyAgent(
                    name="user_proxy",
                    input_func=self.input_func
                )
                termination_en = TextMentionTermination("APPROVE")
                termination_zh = TextMentionTermination("同意")
                # 支持用户对分析报告进行多次修改
                team = RoundRobinGroupChat([agent, user_proxy], termination_condition=termination_en | termination_zh, )
                stream = team.run_stream(task=self._prepare_task(query, schema_context, mappings_str))
                async for msg in stream:
                    # 模拟流式输出
                    if isinstance(msg, ModelClientStreamingChunkEvent):
                        await self.send_response(msg.content)
                        continue
                    # 记录每次对话历史记录
                    if isinstance(msg, TextMessage):
                        # 保存历史记忆
                        await memory.add(MemoryContent(content=msg.model_dump_json(), mime_type=MemoryMimeType.JSON.value))
                        continue
                    # 等待用户输入对分析报告的修改建议
                    if isinstance(msg, UserInputRequestedEvent) and msg.source == "user_proxy":
                        # await self.send_response("请输入修改建议或者直接点击同意")
                        continue
            else:
                # 如果用户没有参与修改，则直接生成分析报告
                stream = agent.run_stream(task=self._prepare_task(query, schema_context, mappings_str))
                async for event in stream:
                    if isinstance(event, ModelClientStreamingChunkEvent):
                        # 确保内容以Markdown格式正确渲染
                        await self.send_response(event.content)
                        continue
                    if isinstance(event, TextMessage):
                        await memory.add(MemoryContent(content=event.model_dump_json(), mime_type=MemoryMimeType.JSON.value))

            await self.send_response("\n\n分析已完成", is_final=True)

            # 序列化内存内容
            memory_content = self.serialize_memory_content(memory)

            analysis_message = AnalysisMessage(
                query=query,
                memory_content=memory_content,
                analysis=analysis_content,
                role="assistant",
                connection_id=connection_id,
                schema_context=schema_context,
                mappings_str=mappings_str
            )

            await self.publish_message(
                analysis_message,
                topic_id=TopicId(type=TopicTypes.SQL_GENERATOR.value, source=self.id.key)
            )
        except Exception as e:
            await self.handle_exception("handle_message", e)

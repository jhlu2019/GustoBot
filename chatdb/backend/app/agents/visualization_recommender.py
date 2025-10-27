"""
可视化推荐智能体
负责建议合适的可视化方式
"""
import json
from typing import Dict, Any

from autogen_core import message_handler, MessageContext, type_subscription
from autogen_agentchat.agents import AssistantAgent

from app.schemas.text2sql import SqlResultMessage, Text2SQLResponse
from .base import BaseAgent
from .types import AgentTypes, AGENT_NAMES, TopicTypes


@type_subscription(topic_type=TopicTypes.VISUALIZATION_RECOMMENDER.value)
class VisualizationRecommenderAgent(BaseAgent):
    """可视化推荐智能体，负责建议合适的可视化方式"""

    def __init__(self, model_client_instance=None, db_type=None):
        """初始化可视化推荐智能体

        Args:
            model_client_instance: 模型客户端实例
            db_type: 数据库类型
        """
        super().__init__(
            agent_id="visualization_recommender_agent",
            agent_name=AGENT_NAMES[AgentTypes.VISUALIZATION_RECOMMENDER.value],
            model_client_instance=model_client_instance,
            db_type=db_type
        )
        self._prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        """构建提示模板"""
        return """
        你是一名专业的数据可视化专家，负责根据提供的用户指令、SQL查询及其结果数据，推荐最合适的数据可视化方式，并给出详细的配置建议。

        ## 规则

        1.  **分析SQL查询：** 理解SQL查询的目标，例如是进行趋势分析、比较不同类别的数据、展示数据分布还是显示详细数据。
        2.  **分析查询结果数据结构：** 检查返回的数据包含哪些字段，它们的数据类型（数值型、分类型等），以及数据的组织方式（例如，是否包含时间序列、类别标签、数值指标等）。
        3.  **基于数据结构和查询目标推荐可视化类型：**
            * 如果数据涉及**时间序列**且需要展示**趋势**，推荐 `"line"` (折线图)。
            * 如果需要**比较不同类别**的**数值大小**，推荐 `"bar"` (柱状图)。
            * 如果需要展示**各部分占总体的比例**，且类别数量不多，推荐 `"pie"` (饼图)。需要确保数值型字段是总量的一部分。
            * 如果需要展示**两个数值变量之间的关系**或**数据点的分布**，推荐 `"scatter"` (散点图)。
            * 如果数据结构复杂、细节重要，或者无法找到合适的图表类型清晰表达，推荐 `"table"` (表格)。
        4.  **提供详细的可视化配置建议：** 根据选择的可视化类型，提供具体的配置参数。
            * **通用配置：** `"title"` (图表标题，应简洁明了地概括图表内容)。
            * **柱状图 (`"bar"`):**
                * `"xAxis"` (X轴字段名，通常是分类型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **折线图 (`"line"`):**
                * `"xAxis"` (X轴字段名，通常是时间或有序的分类型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **饼图 (`"pie"`):**
                * `"nameField"` (名称字段名，通常是分类型字段，用于显示饼图的标签)。
                * `"valueField"` (数值字段名，用于计算每个扇区的大小)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **散点图 (`"scatter"`):**
                * `"xAxis"` (X轴字段名，通常是数值型字段)。
                * `"yAxis"` (Y轴字段名，通常是数值型字段)。
                * `"seriesName"` (系列名称，如果只有一个系列可以省略)。
            * **表格 (`"table"`):** 不需要特定的坐标轴或系列配置，可以考虑添加 `"columns"` 字段，列出需要在表格中显示的字段名。
        5.  **输出格式必须符合如下JSON格式:**

            ```json
            {
                "type": "可视化类型",
                "config": {
                    "title": "图表标题",
                    "xAxis": "X轴字段名",
                    "yAxis": "Y轴字段名",
                    "seriesName": "系列名称"
                    // 其他配置参数根据可视化类型添加
                }
            }
            ```

            对于饼图：

            ```json
            {
                "type": "pie",
                "config": {
                    "title": "图表标题",
                    "nameField": "名称字段名",
                    "valueField": "数值字段名",
                    "seriesName": "系列名称"
                }
            }
            ```

            对于表格：

            ```json
            {
                "type": "table",
                "config": {
                    "title": "数据表格",
                    "columns": ["字段名1", "字段名2", ...]
                }
            }
            ```

        ## 支持的可视化类型

        - `"bar"`: 柱状图
        - `"line"`: 折线图
        - `"pie"`: 饼图
        - `"scatter"`: 散点图
        - `"table"`: 表格(对于不适合图表的数据)
        特别注意：如果用户有对生成的图表有明确的特定要求，一定要严格遵守用户的指令。例如用户明确要求生成饼状图，就不能生成柱状图。
        """

    def _prepare_task(self, message: SqlResultMessage) -> str:
        """准备任务描述

        Args:
            message: SQL结果消息

        Returns:
            str: 任务描述
        """
        # 将结果转换为JSON字符串
        results_json = json.dumps(message.results, ensure_ascii=False)

        return f"""
        ## 用户指令
         {message.query}

        ## 待分析的SQL查询
        {message.sql}

        ## SQL查询结果数据
        ```json
        {results_json}
        ```

        请根据提供的上述信息，分析并输出最合适的可视化类型和配置，输出必须是有效的JSON
        """

    def _parse_visualization_config(self, content: str, fallback_results: list) -> Dict[str, Any]:
        """解析可视化配置

        Args:
            content: LLM返回的内容
            fallback_results: 备用结果数据，用于生成默认配置

        Returns:
            Dict[str, Any]: 可视化配置
        """
        try:
            # 清理JSON字符串，移除可能的标记
            cleaned_json = content.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            print(f"解析可视化配置时出错: {str(e)}")
            # 使用默认配置
            return {
                "type": "bar",
                "config": {
                    "title": "数据可视化",
                    "xAxis": list(fallback_results[0].keys())[0] if fallback_results else "x",
                    "yAxis": list(fallback_results[0].keys())[1] if fallback_results and len(fallback_results[0].keys()) > 1 else "y"
                }
            }

    @message_handler
    async def handle_message(self, message: SqlResultMessage, ctx: MessageContext) -> None:
        """处理接收到的消息，推荐可视化方式"""
        try:
            # 检查是否有错误
            if hasattr(message, 'error') and message.error:
                await self.send_response(f"由于SQL执行错误，无法提供可视化建议: {message.error}")
                await self.send_response("可视化分析已完成", is_final=True)
                return

            # 检查结果是否为空
            if not message.results or len(message.results) == 0:
                await self.send_response("没有数据可供可视化分析")
                await self.send_response("可视化分析已完成", is_final=True)
                return

            # 发送处理中消息
            await self.send_response("正在分析数据，生成可视化建议...")

            # 准备任务描述
            task = self._prepare_task(message)

            # 创建智能体并执行任务
            agent = AssistantAgent(
                name="visualization_recommender",
                model_client=self.model_client,
                system_message=self._prompt,
                model_client_stream=True,
            )

            result = await agent.run(task=task)
            visualization_json = result.messages[-1].content

            # 处理JSON输出
            visualization = self._parse_visualization_config(visualization_json, message.results)

            # 如果是表格，则直接返回，因为表格已经在上个智能体中已经呈现
            if visualization.get("type") == "table":
                await self.send_response("可视化分析已完成", is_final=True)
                return

            # 发送可视化建议
            await self.send_response(
                f"建议使用 {visualization.get('type', 'bar')} 类型进行可视化展示"
            )

            # 构建最终结果
            final_result = Text2SQLResponse(
                sql=message.sql,
                explanation=message.explanation,
                results=message.results,
                visualization_type=visualization.get("type", "bar"),
                visualization_config=visualization.get("config", {})
            )

            # 发送可视化结果到visualization区域
            await self.send_response(
                "可视化分析完成",
                is_final=True,
                result={
                    "visualization_type": visualization.get("type", "bar"),
                    "visualization_config": visualization.get("config", {})
                }
            )

            # 发送完整的最终结果
            await self.send_response(
                "处理完成，返回最终结果",
                is_final=True,
                result=final_result.model_dump()
            )
        except Exception as e:
            await self.handle_exception("handle_message", e)

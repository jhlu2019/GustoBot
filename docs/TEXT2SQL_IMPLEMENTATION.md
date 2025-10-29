# Text2SQL Implementation

基于 LangGraph 的 Text2SQL 系统实现文档。

> **提示**：通过 `docker build` / `docker compose` 启动本项目时，会自动初始化 MySQL 与 Neo4j 样例数据，并将关系模型同步到图数据库，因而可以直接体验 Text2SQL 全流程。

## 📖 概述

当前实现对 ChatDB 的多智能体架构进行了 LangGraph 化改造：

| 能力维度 | ChatDB (AutoGen Agents) | GustoBot (LangGraph Nodes) |
|----------|-------------------------|-----------------------------|
| 框架 | Microsoft AutoGen | LangGraph StateGraph |
| Schema 检索 | SchemaRetrieverAgent | `schema_retrieval.node` (Neo4j 实时查询) |
| 查询意图分析 | QueryAnalyzerAgent | `query_analysis.node` (结构化 JSON 分析) |
| SQL 生成 | SqlGeneratorAgent | `sql_generation.node` (LLM → SQL) |
| SQL 验证 | SqlValidatorAgent | `sql_validation.node` (语法 + 安全) |
| SQL 执行 | SqlExecutorAgent | `sql_execution.node` (SQLAlchemy) |
| 可视化推荐 | VisualizationRecommenderAgent | `visualization.node` (结构化推荐) |
| 答案整理 | Multi-Agent 汇总 | `formatting.node` (统一 Markdown 回复) |
| 重试机制 | LLM 重试 | LangGraph 条件边 + `retry_count` |

## 🏗️ 工作流

```
用户提问
   │
   ▼
Router (lg_builder)
   │ 识别 text2sql-query
   ▼
StateGraph
   ├─ Step 1: Schema Retrieval (Neo4j 表、字段、关系、值映射)
   ├─ Step 2: Query Analysis (LLM 生成结构化分析 & Markdown 摘要)
   ├─ Step 3: SQL Generation (基于分析与 Schema)
   ├─ Step 4: SQL Validation (语法/安全，失败则回到生成重试)
   ├─ Step 5: SQL Execution (只读查询，自动解析 connection_id)
   ├─ Step 6: Visualization Recommendation (结果驱动的图表建议)
   └─ Step 7: Answer Formatting (回复 + SQL + 可视化摘要)
```

## 📂 目录结构

核心代码位于 `gustobot/application/agents/kg_sub_graph/agentic_rag_agents/components/text2sql/`：

```
text2sql/
├── __init__.py                  # 对外导出节点
├── schema_retrieval/            # Schema 检索 (Neo4j)
├── query_analysis/              # 查询意图分析 (LLM JSON)
├── sql_generation/              # SQL 生成与提示词
├── sql_validation/              # 语法 + 安全校验
├── sql_execution/               # 数据库执行层
├── visualization/               # 可视化推荐
└── formatting/                  # 最终答复组装
```

`gustobot/application/agents/text2sql/` 目录继续保留公共接口 (`workflow.py`, `state.py`, `models.py` 等)，同时在 `components/__init__.py` 提供向新的组件目录的兼容包装，外部调用方式保持不变：

```python
from gustobot.application.agents.text2sql import create_text2sql_workflow
workflow = create_text2sql_workflow(llm, neo4j_graph, db_type="MySQL")
result = await workflow.ainvoke({...})
```

## 🔍 组件说明

### Schema Retrieval (`schema_retrieval/node.py`)
- 对应 ChatDB 的 SchemaRetrieverAgent。
- 基于 `connection_id` 查询 Neo4j 中的 `Table` / `Column` / `REFERENCES` / `ValueMapping`。
- 根据用户问题关键词为表打分，限制返回数量，便于 prompt 控制。
- 输出：`schema_context`、`value_mappings`、`mappings_str`。

### Query Analysis (`query_analysis/node.py`)
- 模仿 QueryAnalyzerAgent，利用 LLM 生成 `SQLAnalysis` 模型，结构化包含意图、表、列、连接条件等。
- 生成 Markdown 提要（`analysis_text`），供最终答复展示。

### SQL Generation (`sql_generation/node.py`)
- 结合 Schema 文本、值映射、分析结果与原始问题，生成只读 SQL。
- 使用低温度 (`temperature=0.1`) 确保稳定输出。

### SQL Validation (`sql_validation/node.py`)
- 执行轻量语法检查（括号/引号匹配、仅允许 SELECT 或 WITH 开头）。
- 屏蔽 DROP/DELETE/INSERT/ALTER 等危险操作；失败累计 `retry_count`。

### SQL Execution (`sql_execution/node.py`)
- 根据 `connection_id` 读取 `dbconnection` 信息（Docker 初始化时已导入样例数据）。
- 自动映射不同数据库驱动，仅允许单条只读查询，默认限制返回 `1000` 行。

### Visualization (`visualization/node.py`)
- 分析结果样本，产出结构化 `VisualizationRecommendation`（bar/line/pie/scatter/table）。
- 未能识别时回退为 `table`。

### Answer Formatting (`formatting/node.py`)
- 汇总问题、分析摘要、结果预览、推荐图表配置，以 Markdown 形式返回给用户。
- 同时在 workflow 输出中保留 SQL、查询结果与可视化配置，便于前端渲染。

## 📦 Docker 初始化

- `docker compose up` 会执行数据库迁移脚本，插入演示 `dbconnection` / `schematable` / `schemacolumn` / `valuemapping` 数据。
- 启动后会调用同步脚本，将元数据写入 Neo4j（节点 `Table`、`Column`、`REFERENCES` 与 `HAS_VALUE_MAPPING`）。
- 因此在容器内直接触发 Text2SQL，即可完整运行上述流程，无需手工准备数据。

## 🧠 提示词位置

- 查询分析提示：`components/text2sql/query_analysis/prompts.py`
- SQL 生成提示：`components/text2sql/sql_generation/prompts.py`
- 可视化提示：`components/text2sql/visualization/prompts.py`

## 🔒 安全性

1. 所有查询强制以 SELECT/CTE 开头并拒绝多语句。
2. 明确拒绝 DROP/ALTER/INSERT/UPDATE/DELETE 等破坏性关键字。
3. 默认限制返回行数，避免一次性拉取大量数据。

## ✅ 测试与验证

```bash
python -m compileall gustobot/application/agents/text2sql \
    gustobot/application/agents/kg_sub_graph/agentic_rag_agents/components/text2sql
```

上线前可通过以下方式验证：
1. 运行 docker 环境，确认 MySQL/Neo4j 数据自动导入。
2. 触发一条 Text2SQL 请求，核对日志中新增的 `query_analysis`、`visualization` 步骤。
3. 前端可读取 workflow 输出中的 `visualization_config` 渲染图表。

## 🔜 可选后续

- **SQL 解释**：补充自然语言解释节点，对应 ChatDB 的 SqlExplainerAgent。
- **历史记忆**：将查询命中结果追加到会话记录中，实现多轮深化分析。
- **测试用例**：针对每个节点补充单元测试，使用 Mock Neo4j / Mock DB。

---

完成上述改造后，Text2SQL Pipeline 已经完全 LangGraph 化，并与项目中其他工作流（如 Text2Cypher、Agentic RAG）保持一致的结构组织。

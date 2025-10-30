# Agent 路由测试指南

本指南详细说明如何测试和验证 GustoBot 多 Agent 系统的路由决策和智能子决策流程。

## 目录

1. [测试环境准备](#测试环境准备)
2. [核心路由流程](#核心路由流程)
3. [各路由类型的验证方法](#各路由类型的验证方法)
4. [智能子决策验证](#智能子决策验证)
5. [日志观察要点](#日志观察要点)
6. [常见问题排查](#常见问题排查)

---

## 测试环境准备

### 1. 确保服务正常运行

```bash
# 启动依赖服务
docker-compose up -d neo4j redis milvus mysql

# 启动 FastAPI 服务器
python -m uvicorn gustobot.main:application --reload --host 0.0.0.0 --port 8000
```

### 2. 检查配置

确保 `.env` 文件包含以下关键配置：

```env
# LLM 配置
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o
OPENAI_API_BASE=https://api.openai.com/v1

# Neo4j（图谱）
NEO4J_URI=bolt://localhost:17687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# Milvus（向量数据库）
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=recipe_knowledge

# Redis（缓存和会话）
REDIS_URL=redis://localhost:6379/0

# PostgreSQL（pgvector 可选）
POSTGRES_HOST=localhost
POSTGRES_PORT=15432
POSTGRES_DB=recipe_db

# 知识库配置
KB_TOP_K=5
KB_SIMILARITY_THRESHOLD=0.7
KB_ENABLE_EXTERNAL_SEARCH=false

# Reranker
RERANKER_PROVIDER=cohere  # 或 jina/voyage/bge
RERANKER_API_KEY=your_key
```

### 3. 运行测试脚本

```bash
# 方式1: 运行完整测试套件
python -m tests.test_agent_routing --suite

# 方式2: 快速测试单个问题
python -m tests.test_agent_routing --single "红烧肉怎么做"

# 方式3: 通过 API 测试（配合 Web 界面）
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "红烧肉怎么做", "session_id": "test_001"}'
```

---

## 核心路由流程

### LangGraph 状态图结构

```
START
  ↓
analyze_and_route_query  ← 【核心路由节点】LLM 分类 + 启发式 fallback
  ↓
route_query              ← 【条件分支】根据路由类型分发
  ├─→ respond_to_general_query    (general-query)
  ├─→ get_additional_info         (additional-query)
  ├─→ create_kb_query             (kb-query) 🔹 智能决策点1
  ├─→ create_research_plan        (graphrag-query / text2sql-query) 🔹 智能决策点2
  ├─→ create_image_query          (image-query)
  └─→ create_file_query           (file-query)
  ↓
END
```

### 路由决策逻辑

在 `gustobot/application/agents/lg_builder.py:65` 的 `analyze_and_route_query` 函数中：

1. **第一层**: LLM 路由（使用 `ROUTER_SYSTEM_PROMPT`）
   - 调用 OpenAI API 进行问题分类
   - 返回结构化输出 `Router` (type, logic, question)

2. **第二层**: 启发式 fallback（`_heuristic_router`）
   - 如果 LLM 返回无效类型，使用关键词匹配
   - 关键词规则（`lg_builder.py:918`）:
     ```python
     graphrag_keywords = ["怎么做", "如何做", "做法", "步骤", "火候", "食材", ...]
     text2sql_keywords = ["统计", "多少", "总数", "数量", "排名"]
     ```

3. **第三层**: 默认 fallback
   - 如果以上都失败，默认 `kb-query`

### 配置优先级拦截

在 `route_query` 函数中（`lg_builder.py:169`）：

```python
if cfg.get("image_path"):
    return "create_image_query"  # 强制图片路由
if cfg.get("file_path"):
    return "create_file_query"   # 强制文件路由
```

---

## 各路由类型的验证方法

### 1. General-Query（闲聊/问候）

**触发条件**:
- 问候、寒暄、情绪反馈
- 与菜谱无关的简短对话

**验证步骤**:
```bash
# 测试问题
问: "你好"
问: "谢谢你的帮助"
问: "今天心情不错"
```

**预期日志**:
```
INFO - -----Analyze user query type-----
INFO - Analyze user query type completed, result: {'type': 'general-query', 'logic': '...', 'question': '你好'}
INFO - -----generate general-query response-----
```

**验证要点**:
- ✅ 路由类型为 `general-query`
- ✅ 回复包含"亲～"或"厨友您好～"
- ✅ 使用礼貌用语和 emoji
- ✅ 无调用知识库或图谱

---

### 2. Additional-Query（补充信息）

**触发条件**:
- 问题模糊，缺少关键信息
- 需要询问菜名、食材、份量等细节

**验证步骤**:
```bash
# 测试问题
问: "我想做菜"
问: "这个菜怎么做好吃"
问: "这个菜热量高吗"
```

**预期日志**:
```
INFO - Analyze user query type completed, result: {'type': 'additional-query', ...}
INFO - ------continue to get additional info------
INFO - success to get Neo4j graph database connection
INFO - -----Pass guardrails check-----  # 或 -----Fail to pass guardrails check-----
```

**验证要点（Guardrails 子决策）**:

#### 场景A: 菜谱相关但信息不足
```python
# guardrails_output.decision == "proceed"
问: "我想做菜"
预期: 询问"您想做哪道菜呢？"
```

#### 场景B: 无关问题
```python
# guardrails_output.decision == "end"
问: "今天天气怎么样"
预期: "厨友您好～抱歉哦，这个问题不太属于我们的菜谱范围呢"
```

**关键代码** (`lg_builder.py:310`):
```python
guardrails_chain = full_system_prompt | model.with_structured_output(AdditionalGuardrailsOutput)
guardrails_output: AdditionalGuardrailsOutput = await guardrails_chain.ainvoke(...)

if guardrails_output.decision == "end":
    return {"messages": [AIMessage(content="...不太属于我们的菜谱范围...")]}
else:
    # 继续询问补充信息
```

---

### 3. KB-Query（向量知识库检索）

**触发条件**:
- 菜谱历史、典故、流派介绍
- 菜品背景、名厨偏好、地域文化
- 食材营养科普

**验证步骤**:
```bash
# 测试问题
问: "宫保鸡丁的历史典故是什么"
问: "川菜的特点是什么"
问: "西兰花有什么营养价值"
```

**预期日志**:
```
INFO - Analyze user query type completed, result: {'type': 'kb-query', ...}
INFO - ------execute KB multi-tool query------
INFO - [KB Multi-Tool Workflow] Starting workflow
INFO - [KB Multi-Tool Workflow] Guardrails check passed
INFO - [KB Multi-Tool Workflow] Router selected tools: ['milvus', 'pgvector']  🔹 智能决策
INFO - [KB Multi-Tool Workflow] Milvus retrieval: 5 results
INFO - [KB Multi-Tool Workflow] PostgreSQL retrieval: 3 results
INFO - [KB Multi-Tool Workflow] Reranker processing: 8 → 5 results
INFO - [KB Multi-Tool Workflow] Finalizer generating answer
```

**智能子决策验证点**:

#### 决策点1: 工具选择（`kb_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`）

Router 节点会根据问题类型选择工具：
```python
# 可能的工具组合：
['milvus']              # 仅 Milvus 向量检索
['pgvector']            # 仅 PostgreSQL pgvector
['milvus', 'pgvector']  # 两者都查询（高优先级问题）
['milvus', 'external']  # Milvus + 外部搜索（配置允许时）
```

**验证方法**:
- 观察日志中的 `Router selected tools: [...]`
- 检查是否根据问题复杂度动态选择
- 高优先级/复杂问题应触发多源检索

#### 决策点2: Reranker 重排序

当多个来源返回结果时，Reranker 会合并并重新排序：
```
Milvus: 5 results (初始召回)
+ pgvector: 3 results
= 8 results (合并)
→ Reranker (Cohere/Jina/Voyage/BGE)
→ 5 results (最终 top_k)
```

**验证方法**:
- 检查日志中的 `Reranker processing: X → Y results`
- 对比重排序前后的结果顺序变化

#### 决策点3: Fallback 降级

如果 Multi-tool workflow 初始化失败：
```python
# lg_builder.py:717
except Exception as exc:
    logger.warning("KB multi-tool workflow unavailable (%s); falling back to direct search.", exc)
    # 降级到直接 KB 查询
    knowledge_node = create_knowledge_query_node(knowledge_service=KnowledgeService())
```

**验证方法**:
- 故意关闭 Milvus 或 PostgreSQL
- 观察是否触发 fallback 并返回部分结果

---

### 4. GraphRAG-Query（图谱推理 + 多工具）

**触发条件**:
- 询问菜谱的做法、步骤细节、火候掌握
- 询问食材用量、所需原料、准备方法
- 询问烹饪技巧、判断熟度、失败排查
- 需要从图谱/数据库综合汇总信息

**验证步骤**:
```bash
# 测试问题（不同子决策路径）
问: "红烧肉怎么做"                     # → Cypher
问: "宫保鸡丁需要哪些食材"              # → Predefined Cypher
问: "炒青菜怎么保持翠绿"                # → Cypher + GraphRAG
问: "怎么判断鱼熟了"                   # → GraphRAG
问: "为什么我做的红烧肉发柴"            # → GraphRAG + Cypher
问: "什么菜适合感冒的人吃"              # → Multiple Tools
```

**预期日志**:
```
INFO - Analyze user query type completed, result: {'type': 'graphrag-query', ...}
INFO - ------execute local knowledge base query------
INFO - success to get Neo4j graph database connection
INFO - [Multi-Tool Workflow] Starting workflow
INFO - [Planner] Analyzing question and selecting tools  🔹 智能决策
INFO - [Planner] Selected tools: ['cypher_query', 'microsoft_graphrag_query']
INFO - [Tool Executor] Executing cypher_query
INFO - [Cypher Retriever] Generated Cypher: MATCH (d:Dish {name: "红烧肉"})-[:HAS_STEP]->...
INFO - [Tool Executor] Executing microsoft_graphrag_query
INFO - [GraphRAG] Local search mode
INFO - [Finalizer] Combining 2 tool results
INFO - [Finalizer] Final answer generated
```

**智能子决策验证点**:

#### 决策点1: Planner 工具选择

Planner 节点（`kg_sub_graph/agentic_rag_agents/components/planner/node.py`）会分析问题并选择工具：

```python
# 可用工具（定义在 lg_builder.py:775）
tool_schemas = [
    cypher_query,              # 动态生成 Cypher（通用查询）
    predefined_cypher,         # 预定义 Cypher 模板（高频场景）
    microsoft_graphrag_query,  # GraphRAG 图推理（需要推理的问题）
    text2sql_query,            # 结构化数据库查询（统计类）
]
```

**工具选择逻辑**（Planner 内部）:

| 问题类型 | 优先工具 | 原因 |
|---------|---------|------|
| "红烧肉怎么做" | `predefined_cypher` | 做法查询是高频场景，有预定义模板 |
| "什么菜含牛肉" | `cypher_query` | 需要动态生成 `MATCH (d:Dish)-[:HAS_INGREDIENT]->...` |
| "怎么判断鱼熟了" | `microsoft_graphrag_query` | 需要推理经验知识，非结构化 |
| "数据库里有多少道菜" | `text2sql_query` | 统计查询，需要 SQL |
| "什么菜适合感冒吃" | `cypher_query` + `microsoft_graphrag_query` | 综合图谱关系 + 推理 |

**验证方法**:
- 观察日志中的 `[Planner] Selected tools: [...]`
- 检查不同问题类型是否触发正确的工具组合
- 复杂问题应触发多工具并行

#### 决策点2: Cypher 生成方式

**方式A: Predefined Cypher（预定义模板）**

```python
# kg_sub_graph/agentic_rag_agents/components/predefined_cypher/cypher_dict.py
predefined_cypher_dict = {
    "菜谱做法": "MATCH (d:Dish {name: $dish_name})-[:HAS_STEP]->(s:CookingStep) RETURN ...",
    "食材查询": "MATCH (d:Dish {name: $dish_name})-[:HAS_INGREDIENT]->(i:Ingredient) RETURN ...",
    "口味特点": "MATCH (d:Dish)-[:HAS_FLAVOR]->(f:Flavor) WHERE f.name = $flavor RETURN ...",
    # ... 更多预定义模板
}
```

**验证日志**:
```
INFO - [Predefined Cypher] Matched template: 菜谱做法
INFO - [Predefined Cypher] Executing: MATCH (d:Dish {name: "红烧肉"})-[:HAS_STEP]->...
```

**方式B: Dynamic Cypher（LLM 动态生成）**

使用 LLM + Few-shot Examples 生成：
```python
# cypher_example_retriever = RecipeCypherRetriever()
# 从向量库检索相似的 Cypher 示例作为 prompt
```

**验证日志**:
```
INFO - [Cypher Query] Retrieving examples for question: ...
INFO - [Cypher Query] Found 3 similar examples
INFO - [Cypher Query] LLM generated Cypher: MATCH (d:Dish)...
INFO - [Cypher Validation] Syntax check passed
INFO - [Cypher Query] Executing against Neo4j
```

**Cypher 验证机制**（`llm_cypher_validation=True`）:
- LLM 生成后进行语法检查
- 如果无效，重新生成（最多重试1次）
- 失败则降级到 GraphRAG 或返回错误

**验证方法**:
- 故意提问边缘 case（如生僻菜名）
- 观察是否触发 Cypher 验证和重试
- 检查最终执行的 Cypher 是否正确

#### 决策点3: GraphRAG 查询模式

Microsoft GraphRAG（LightRAG）支持两种模式：

```python
# gustobot/graphrag/dev/graphrag_query.py
search_mode = "local"   # 局部搜索（默认，快速）
# 或
search_mode = "global"  # 全局搜索（慢，适合大范围问题）
```

**验证日志**:
```
INFO - [GraphRAG] Using search mode: local
INFO - [GraphRAG] Query: 怎么判断鱼熟了
INFO - [GraphRAG] Retrieved entities: ['鱼', '烹饪', '熟度判断', ...]
INFO - [GraphRAG] Graph reasoning completed
```

**验证方法**:
- 观察不同问题是否触发不同模式
- 局部问题（单个菜谱）→ local
- 全局问题（菜系比较）→ global

#### 决策点4: Text2SQL 动态生成

当问题涉及统计、数量时：

**验证日志**:
```
INFO - [Text2SQL] Question requires database query
INFO - [Text2SQL] Available tables: recipes, ingredients, nutrition
INFO - [Text2SQL] LLM generated SQL: SELECT COUNT(*) FROM recipes WHERE category = '川菜'
INFO - [Text2SQL] Executing against MySQL
INFO - [Text2SQL] Result: 128 records
```

**验证方法**:
- 检查生成的 SQL 语法是否正确
- 验证结果数字与实际数据库一致
- 测试复杂 SQL（JOIN, GROUP BY）

#### 决策点5: Finalizer 结果融合

当多个工具返回结果时，Finalizer 会：
1. 合并所有来源的数据
2. 去重和排序
3. 用 LLM 生成统一回答

**验证日志**:
```
INFO - [Finalizer] Combining results from 2 tools
INFO - [Finalizer] Source 1 (cypher_query): 5 results
INFO - [Finalizer] Source 2 (microsoft_graphrag_query): 3 results
INFO - [Finalizer] Merged and deduplicated: 7 unique results
INFO - [Finalizer] LLM generating coherent answer
INFO - [Finalizer] Final answer: "红烧肉的做法如下：1. 切块... 2. 焯水... (来源: Neo4j图谱 + GraphRAG推理)"
```

**验证方法**:
- 观察是否标注了数据来源
- 检查回答是否融合了多个工具的信息
- 验证是否有重复或矛盾内容

---

### 5. Text2SQL-Query（启发式路由）

**触发条件**:
- 启发式关键词："统计"、"多少"、"总数"、"数量"、"排名"
- LLM 也可能直接分类为 `text2sql-query`

**验证步骤**:
```bash
# 测试问题
问: "数据库里有多少道菜"
问: "哪个菜系的菜谱最多"
问: "统计每个口味的菜谱数量"
```

**预期日志**:
```
INFO - Analyze user query type completed, result: {'type': 'text2sql-query', 'logic': 'keyword fallback: text2sql', ...}
# 或
INFO - Analyze user query type completed, result: {'type': 'graphrag-query', ...}  # LLM 分类到 graphrag
INFO - ------execute local knowledge base query------
INFO - [Planner] Selected tools: ['text2sql_query']  # Planner 二次分类
INFO - [Text2SQL] Generating SQL query
```

**验证要点**:
- ✅ 启发式关键词正确触发 `text2sql-query`
- ✅ 如果进入 `graphrag-query`，Planner 应选择 `text2sql_query` 工具
- ✅ 生成的 SQL 语法正确且安全（防 SQL 注入）
- ✅ 返回准确的统计数字

---

### 6. Image-Query（图片识别/生成）

**触发条件**:
- 配置中提供 `image_path`（强制优先）
- LLM 分类为 `image-query`
- 生成关键词："生成"、"画"、"创建"、"来一张"

**验证步骤**:
```bash
# 图片识别
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "这是什么菜", "image_path": "/tmp/dish.jpg"}'

# 图片生成
python -m tests.test_agent_routing --single "生成一张红烧肉的图片"
```

**预期日志**:

#### 识别模式:
```
INFO - -----Handle Image Query-----
INFO - User Upload Image Path: /tmp/dish.jpg
INFO - Using Vision Model: gpt-4o-vision to process image
INFO - Image Compressed, Original Size: 2048x1536, New Size: 1024x768
INFO - Successfully processed image and generated description
INFO - Image description: 这是一道红烧肉，色泽红亮，肥瘦相间...
```

#### 生成模式:
```
INFO - Image Generation Request: 生成一张红烧肉的图片
INFO - Enhancing user prompt: 生成一张红烧肉的图片
INFO - Enhanced prompt: 商业美食摄影，特写镜头，一盘精美的红烧肉，色泽红亮...
INFO - Calling CogView-4 API: https://api.example.com/images/generations
INFO - CogView-4 API response: {"data": [{"url": "https://..."}]}
INFO - Image generated successfully: https://...
```

**验证要点**:
- ✅ 识别模式正确调用 Vision API
- ✅ 生成模式先用 LLM 优化提示词
- ✅ 图片压缩逻辑（大于1024px自动缩放）
- ✅ 返回图片 URL 或 base64

---

### 7. File-Query（文件上传）

**触发条件**:
- 配置中提供 `file_path`（强制优先）
- LLM 分类为 `file-query`

**验证步骤**:
```bash
# 文本文件
echo "宫保鸡丁的做法：1. 切块..." > /tmp/recipe.txt
python -m tests.test_agent_routing --single "帮我分析这个菜谱文件" --file-path /tmp/recipe.txt

# Excel 文件（需要外部 Ingest Service）
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "导入这个菜谱 Excel", "file_path": "/tmp/recipes.xlsx"}'
```

**预期日志**:
```
INFO - -----Found User Upload File-----
INFO - User Upload File Path: /tmp/recipe.txt
INFO - File size: 1024 bytes (< 10MB limit)
INFO - File type: .txt (text file)
INFO - Reading file content
INFO - Adding document to knowledge base: upload_recipe_abc123
INFO - [Knowledge Query] Querying KB with question: 帮我分析这个菜谱文件
INFO - [Knowledge Query] Retrieved 3 relevant chunks
```

**验证要点**:
- ✅ 支持的文件类型：.txt/.md/.json/.csv/.log/.xlsx/.xls
- ✅ 文件大小限制检查（默认10MB）
- ✅ 文本文件直接导入知识库
- ✅ Excel 文件调用外部 Ingest Service
- ✅ 导入后立即回答相关问题

---

## 日志观察要点

### 1. 核心路由日志

位置：`gustobot/application/agents/lg_builder.py:96`

```python
logger.info("-----Analyze user query type-----")
logger.info(f"History messages: {state.messages}")
# ... LLM 调用 ...
logger.info(f"Analyze user query type completed, result: {sanitized_router}")
```

**关键字段**:
- `type`: 路由类型（7种之一）
- `logic`: 分类逻辑（LLM 或 keyword fallback 或 default）
- `question`: 标准化后的问题

### 2. KB Multi-tool Workflow 日志

位置：`gustobot/application/agents/kg_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`

```python
logger.info("[KB Multi-Tool Workflow] Starting workflow")
logger.info("[KB Multi-Tool Workflow] Guardrails check passed")
logger.info(f"[KB Multi-Tool Workflow] Router selected tools: {selected_tools}")
logger.info(f"[KB Multi-Tool Workflow] Milvus retrieval: {len(milvus_results)} results")
logger.info(f"[KB Multi-Tool Workflow] PostgreSQL retrieval: {len(pg_results)} results")
logger.info(f"[KB Multi-Tool Workflow] Reranker processing: {before_count} → {after_count} results")
logger.info("[KB Multi-Tool Workflow] Finalizer generating answer")
```

### 3. GraphRAG Multi-tool Workflow 日志

位置：`gustobot/application/agents/kg_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`

```python
logger.info("[Multi-Tool Workflow] Starting workflow")
logger.info("[Planner] Analyzing question and selecting tools")
logger.info(f"[Planner] Selected tools: {tool_list}")
logger.info(f"[Tool Executor] Executing {tool_name}")
logger.info("[Cypher Retriever] Generated Cypher: ...")
logger.info("[GraphRAG] Local search mode")
logger.info("[Text2SQL] Generated SQL: ...")
logger.info(f"[Finalizer] Combining results from {len(sources)} tools")
```

### 4. Guardrails 日志

位置：`gustobot/application/agents/lg_builder.py:316`

```python
if guardrails_output.decision == "end":
    logger.info("-----Fail to pass guardrails check-----")
else:
    logger.info("-----Pass guardrails check-----")
```

### 5. Fallback 日志

位置：`gustobot/application/agents/lg_builder.py:123, 718`

```python
logger.warning("Router LLM failed: %s. Falling back to KB query.", exc)
# 或
logger.warning("KB multi-tool workflow unavailable (%s); falling back to direct search.", exc)
```

---

## 常见问题排查

### 问题1: 路由错误（应该是 graphrag-query 但被分类为 kb-query）

**排查步骤**:
1. 检查 `ROUTER_SYSTEM_PROMPT`（`lg_prompts.py:7`）是否清晰
2. 观察日志中的 `logic` 字段，看 LLM 的判断理由
3. 如果是 keyword fallback，检查 `_heuristic_router`（`lg_builder.py:918`）关键词列表
4. 临时解决：在问题中增加明确关键词（如"怎么做"、"步骤"）

### 问题2: KB Multi-tool 只选择了单一工具（未触发多源检索）

**可能原因**:
- Router 节点判断问题简单，单一来源足够
- Milvus 或 PostgreSQL 服务未启动
- 配置中禁用了某个来源

**排查步骤**:
1. 检查日志 `[KB Multi-Tool Workflow] Router selected tools`
2. 验证 Milvus 和 PostgreSQL 连接状态
3. 检查 `.env` 中的 `KB_ENABLE_EXTERNAL_SEARCH` 配置
4. 尝试更复杂的问题（如"川菜的历史和代表菜品"）

### 问题3: GraphRAG Planner 未选择预期工具

**可能原因**:
- Planner 的提示词不够明确
- LLM 模型温度过高（temperature）
- 工具描述（`tool_schemas`）不够清晰

**排查步骤**:
1. 检查 `kg_sub_graph/agentic_rag_agents/components/planner/prompts.py` 的 prompt
2. 验证工具的 `description` 字段（`kg_tools_list.py`）
3. 降低 LLM 温度（`lg_builder.py:758`）
4. 手动指定工具（测试模式）

### 问题4: Cypher 生成失败或语法错误

**可能原因**:
- Few-shot examples 不足或不相关
- Graph schema 未正确解析
- LLM 幻觉生成错误 Cypher

**排查步骤**:
1. 检查 `RecipeCypherRetriever` 是否有相似示例
2. 验证 Neo4j 连接和 schema 解析
3. 观察日志中的 `[Cypher Validation] Syntax check`
4. 启用 `llm_cypher_validation=True`（默认已启用）
5. 手动测试生成的 Cypher 在 Neo4j Browser 中是否可执行

### 问题5: Text2SQL 统计数字不准确

**可能原因**:
- SQL 生成逻辑错误（如缺少 WHERE 条件）
- 数据库表结构不匹配
- 数据本身有问题

**排查步骤**:
1. 检查日志中的生成 SQL
2. 在 MySQL 客户端手动执行 SQL，验证结果
3. 检查 `text2sql_query` 工具的 table schema 描述
4. 更新 prompt 以包含正确的表结构

### 问题6: Finalizer 回答质量差（多源融合不佳）

**可能原因**:
- 来源数据冲突或重复
- Finalizer prompt 不够强调融合
- LLM 模型能力不足

**优化方法**:
1. 增强 Finalizer prompt（`kg_sub_graph/agentic_rag_agents/components/finalizer/prompts.py`）
2. 添加数据去重和一致性检查
3. 使用更强的 LLM 模型（如 GPT-4o）
4. 在 prompt 中明确要求标注来源

---

## 高级测试场景

### 1. 并发测试（压力测试）

```python
import asyncio

async def concurrent_test():
    tasks = [
        test_routing("红烧肉怎么做"),
        test_routing("川菜的特点是什么"),
        test_routing("数据库里有多少道菜"),
        test_routing("生成一张宫保鸡丁的图片"),
        test_routing("你好"),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 多轮对话测试

```python
# 测试会话上下文保持
session_id = "multi_turn_test"

# 第1轮
test_routing("你好", session_id=session_id)
# 预期: general-query

# 第2轮
test_routing("我想做川菜", session_id=session_id)
# 预期: additional-query（询问具体菜名）

# 第3轮
test_routing("宫保鸡丁", session_id=session_id)
# 预期: graphrag-query（基于上下文理解为"宫保鸡丁怎么做"）

# 第4轮
test_routing("需要多少鸡肉", session_id=session_id)
# 预期: graphrag-query（基于上下文查询宫保鸡丁的食材用量）
```

### 3. 边界 case 测试

```python
# 空输入
test_routing("")
# 预期: 友好提示"请告诉我具体的问题"

# 超长输入
test_routing("怎么做" * 1000)
# 预期: 正常处理或截断提示

# 特殊字符
test_routing("红烧肉怎么做？！@#$%^&*()")
# 预期: 忽略特殊字符，正常路由到 graphrag-query

# 多语言混合
test_routing("How to make 红烧肉?")
# 预期: 正常理解并路由
```

### 4. 性能基准测试

```python
import time

# 测试各路由类型的响应时间
test_cases = [
    ("你好", "general-query"),
    ("宫保鸡丁的历史", "kb-query"),
    ("红烧肉怎么做", "graphrag-query"),
    ("数据库里有多少道菜", "text2sql-query"),
]

for question, expected_route in test_cases:
    start = time.time()
    result = await test_routing(question)
    elapsed = time.time() - start
    print(f"{expected_route}: {elapsed:.2f}s")

# 预期性能基准（参考）:
# general-query: < 1s
# kb-query: 2-5s (depending on reranker)
# graphrag-query: 3-10s (depending on tool complexity)
# text2sql-query: 2-4s
```

---

## 总结

本指南提供了全面的测试方法和验证要点。关键是观察日志输出，确保：

1. **路由准确性**: 每个问题被正确分类到 7 种类型之一
2. **智能决策有效性**: KB Multi-tool 和 GraphRAG Multi-tool 的子决策合理
3. **Fallback 机制**: 异常情况触发降级逻辑，不崩溃
4. **回答质量**: 返回的答案准确、完整、来源可追溯

通过系统化测试，可以持续优化 prompt、工具选择逻辑和融合策略，提升整体系统的智能水平。

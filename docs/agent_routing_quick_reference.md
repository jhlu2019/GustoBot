# Agent 路由快速参考表

快速查询表：每种问题类型的预期路由和智能决策路径

---

## 📋 快速查询表

| 问题示例 | 预期路由 | 主要节点 | 智能子决策 | 数据来源 |
|---------|---------|---------|-----------|---------|
| **你好** | `general-query` | `respond_to_general_query` | - | LLM 直接生成 |
| **早上好** | `general-query` | `respond_to_general_query` | - | LLM 直接生成 |
| **谢谢你** | `general-query` | `respond_to_general_query` | - | LLM 直接生成 |
| **今天心情不错** | `general-query` | `respond_to_general_query` | - | LLM 直接生成 |
| **我想做菜** | `additional-query` | `get_additional_info` | Guardrails → proceed | LLM 询问细节 |
| **这个菜怎么做** | `additional-query` | `get_additional_info` | Guardrails → proceed | LLM 询问菜名 |
| **这个菜热量高吗** | `additional-query` | `get_additional_info` | Guardrails → proceed | LLM 询问菜名 |
| **今天天气怎么样** | `additional-query` | `get_additional_info` | Guardrails → **end** | 礼貌拒绝 |
| **宫保鸡丁的历史典故** | `kb-query` | `create_kb_query` | Router → [milvus, pgvector] → Reranker | Milvus + pgvector |
| **川菜的特点** | `kb-query` | `create_kb_query` | Router → [milvus] | Milvus 向量检索 |
| **佛跳墙的由来** | `kb-query` | `create_kb_query` | Router → [milvus, pgvector] | 多源融合 |
| **西兰花的营养价值** | `kb-query` | `create_kb_query` | Router → [milvus] → Reranker | Milvus + Reranker |
| **红烧肉怎么做** | `graphrag-query` | `create_research_plan` | Planner → [**predefined_cypher**] | Neo4j (预定义) |
| **宫保鸡丁需要哪些食材** | `graphrag-query` | `create_research_plan` | Planner → [**predefined_cypher**] | Neo4j (HAS_INGREDIENT) |
| **炒青菜怎么保持翠绿** | `graphrag-query` | `create_research_plan` | Planner → [cypher_query, microsoft_graphrag] | Neo4j + GraphRAG |
| **怎么判断鱼熟了** | `graphrag-query` | `create_research_plan` | Planner → [**microsoft_graphrag**] | LightRAG 图推理 |
| **为什么红烧肉发柴** | `graphrag-query` | `create_research_plan` | Planner → [cypher_query, microsoft_graphrag] | Neo4j + GraphRAG |
| **什么菜适合感冒吃** | `graphrag-query` | `create_research_plan` | Planner → [cypher_query, microsoft_graphrag] | Neo4j (HEALTH_BENEFIT) + GraphRAG |
| **数据库里有多少道菜** | `text2sql-query` | `create_research_plan` | Planner → [**text2sql_query**] | MySQL (SELECT COUNT) |
| **哪个菜系菜谱最多** | `text2sql-query` | `create_research_plan` | Planner → [**text2sql_query**] | MySQL (GROUP BY) |
| **统计每个口味的数量** | `text2sql-query` | `create_research_plan` | Planner → [**text2sql_query**] | MySQL (GROUP BY) |
| **麻辣口味的菜有多少** | `graphrag-query` | `create_research_plan` | Planner → [cypher_query, text2sql_query] | Neo4j + MySQL |
| **生成红烧肉的图片** | `image-query` | `create_image_query` | LLM 优化 prompt → CogView-4 | 图片生成 API |
| **这是什么菜（附图）** | `image-query` | `create_image_query` | Vision API 识别 → 描述 | 视觉模型 |
| **分析菜谱文件（.txt）** | `file-query` | `create_file_query` | 读取 → 导入 KB → 查询 | 文件 + Milvus |

---

## 🎯 路由类型速查

### 1️⃣ General-Query（闲聊）
- **触发词**: 问候、感谢、情绪表达
- **无需**: 任何数据库查询
- **响应**: LLM 直接生成礼貌回复

### 2️⃣ Additional-Query（补充信息）
- **触发词**: 模糊问题、缺少关键词
- **子决策**: **Guardrails** 检查是否相关
  - `proceed` → 询问补充信息
  - `end` → 礼貌拒绝
- **响应**: 引导式提问

### 3️⃣ KB-Query（向量知识库）
- **触发词**: 历史、典故、背景、文化、流派
- **子决策**: **KB Multi-tool Router** 选择
  - `[milvus]` → 单一向量检索
  - `[pgvector]` → PostgreSQL 向量检索
  - `[milvus, pgvector]` → 多源检索 + **Reranker**
  - `[milvus, external]` → 向量检索 + 外部搜索
- **响应**: 知识科普、背景介绍

### 4️⃣ GraphRAG-Query（图谱推理）
- **触发词**: 怎么做、步骤、食材、火候、技巧
- **子决策**: **Planner** 选择工具组合
  - `[predefined_cypher]` → 高频场景（做法、食材）
  - `[cypher_query]` → 动态生成 Cypher（通用查询）
  - `[microsoft_graphrag_query]` → 需要推理（技巧、判断）
  - `[cypher_query, microsoft_graphrag_query]` → 综合（失败排查）
  - `[cypher_query, text2sql_query]` → 图谱 + 统计
- **响应**: 结构化步骤、推理建议

### 5️⃣ Text2SQL-Query（结构化数据）
- **触发词**: 统计、多少、总数、数量、排名
- **启发式**: 关键词直接路由（fallback）
- **子决策**: **Text2SQL Generator** 生成 SQL
  - `SELECT COUNT(*)` → 统计总数
  - `GROUP BY ... ORDER BY` → 排名/趋势
  - `JOIN` → 多表关联
- **响应**: 数字、统计表

### 6️⃣ Image-Query（图片）
- **识别模式**: Vision API → 描述 → LLM 回答
- **生成模式**: LLM 优化 prompt → CogView-4 → 图片 URL
- **响应**: 图片描述 或 图片链接

### 7️⃣ File-Query（文件上传）
- **文本文件**: 读取 → 导入 KB → 查询回答
- **Excel 文件**: 外部 Ingest Service
- **响应**: 文件已导入 + 相关回答

---

## 🔀 智能决策流程图

### KB-Query 决策流程
```
用户问题（kb-query）
    ↓
create_kb_query
    ↓
KB Multi-tool Workflow
    ↓
┌─────────────────┐
│  Guardrails     │ ✅ proceed / ❌ end
└─────────────────┘
    ↓ proceed
┌─────────────────┐
│  Router         │ → 选择工具: [milvus] / [pgvector] / [milvus, pgvector]
└─────────────────┘
    ↓
┌─────────────────┐
│  Milvus Query   │ → 5 results
└─────────────────┘
    +
┌─────────────────┐
│ pgvector Query  │ → 3 results
└─────────────────┘
    ↓
┌─────────────────┐
│   Reranker      │ → 8 results → 5 results (top_k)
└─────────────────┘
    ↓
┌─────────────────┐
│   Finalizer     │ → LLM 生成回答
└─────────────────┘
```

### GraphRAG-Query 决策流程
```
用户问题（graphrag-query）
    ↓
create_research_plan
    ↓
Multi-tool Workflow
    ↓
┌─────────────────┐
│    Planner      │ → 分析问题并选择工具
└─────────────────┘
    ↓
    ├─→ [predefined_cypher] → Neo4j (高频场景)
    ├─→ [cypher_query] → LLM 生成 Cypher → Neo4j
    ├─→ [microsoft_graphrag_query] → LightRAG 图推理
    └─→ [text2sql_query] → LLM 生成 SQL → MySQL
    ↓
┌─────────────────┐
│ Tool Executor   │ → 并行执行工具
└─────────────────┘
    ↓
┌─────────────────┐
│   Finalizer     │ → 融合多源结果 → LLM 生成回答
└─────────────────┘
```

### Additional-Query 决策流程
```
用户问题（additional-query）
    ↓
get_additional_info
    ↓
┌─────────────────┐
│  Guardrails     │ → 问题是否相关？
└─────────────────┘
    ↓
    ├─→ ✅ proceed → 友好询问补充信息
    └─→ ❌ end → 礼貌拒绝："不太属于我们的菜谱范围"
```

---

## 🧪 测试命令速查

### 运行完整测试套件
```bash
python -m tests.test_agent_routing --suite
```

### 测试单个问题
```bash
python -m tests.test_agent_routing --single "红烧肉怎么做"
```

### 通过 API 测试
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "红烧肉怎么做", "session_id": "test_001"}'
```

### 测试带图片
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "这是什么菜", "image_path": "/tmp/dish.jpg", "session_id": "test_002"}'
```

### 测试文件上传
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "分析这个菜谱", "file_path": "/tmp/recipe.txt", "session_id": "test_003"}'
```

---

## 📊 预期性能基准

| 路由类型 | 平均响应时间 | 主要耗时 |
|---------|-------------|---------|
| general-query | < 1s | LLM 生成 |
| additional-query | 1-2s | Guardrails 检查 + LLM |
| kb-query | 2-5s | 向量检索 + Reranker |
| graphrag-query (Cypher) | 3-7s | Cypher 生成 + Neo4j 查询 |
| graphrag-query (GraphRAG) | 5-10s | LightRAG 图推理 |
| text2sql-query | 2-4s | SQL 生成 + MySQL 查询 |
| image-query (识别) | 3-6s | Vision API 调用 |
| image-query (生成) | 10-20s | Prompt 优化 + CogView-4 |
| file-query | 2-5s | 文件读取 + KB 导入 |

---

## 🔍 日志关键字速查

### 路由日志
```
INFO - -----Analyze user query type-----
INFO - Analyze user query type completed, result: {'type': '...', 'logic': '...'}
```

### KB Multi-tool 日志
```
INFO - [KB Multi-Tool Workflow] Router selected tools: [...]
INFO - [KB Multi-Tool Workflow] Milvus retrieval: X results
INFO - [KB Multi-Tool Workflow] Reranker processing: X → Y results
```

### GraphRAG Multi-tool 日志
```
INFO - [Planner] Selected tools: [...]
INFO - [Cypher Query] Generated Cypher: ...
INFO - [GraphRAG] Local search mode
INFO - [Text2SQL] Generated SQL: ...
INFO - [Finalizer] Combining X tool results
```

### Guardrails 日志
```
INFO - -----Pass guardrails check-----
INFO - -----Fail to pass guardrails check-----
```

### Fallback 日志
```
WARN - Router LLM failed: ... Falling back to KB query.
WARN - KB multi-tool workflow unavailable ... falling back to direct search.
```

---

## ✅ 快速验证清单

在测试时，确保以下行为符合预期：

- [ ] **打招呼问题** → general-query（无 KB 调用）
- [ ] **模糊问题** → additional-query → Guardrails 检查
- [ ] **历史文化问题** → kb-query → 多源检索 + Reranker
- [ ] **菜谱做法** → graphrag-query → Planner 选 predefined_cypher
- [ ] **烹饪技巧** → graphrag-query → Planner 选 GraphRAG
- [ ] **统计数字** → text2sql-query → SQL 查询
- [ ] **无关问题** → Guardrails 拦截 → 礼貌拒绝
- [ ] **异常情况** → Fallback 降级 → 不崩溃

---

## 📚 相关文档

- **完整测试问题集**: `tests/test_agent_routing_questions.md`
- **详细测试指南**: `docs/agent_routing_test_guide.md`
- **测试脚本**: `tests/test_agent_routing.py`
- **路由代码**: `gustobot/application/agents/lg_builder.py`
- **Prompt 定义**: `gustobot/application/agents/lg_prompts.py`
- **多工具流程**: `gustobot/application/agents/kg_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`

---

**使用建议**: 将此表格作为快速参考，遇到问题时查阅详细指南。

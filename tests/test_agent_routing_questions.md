# GustoBot Agent 路由测试问题集

本文档提供了一套全面的测试问题，用于验证 LangGraph 多 Agent 系统的路由和智能决策是否按预期工作。

## 测试说明

- **目标**: 验证每个路由类型的准确性和智能决策的有效性
- **测试方法**: 依次提问，观察日志输出中的路由类型和执行路径
- **预期日志**: 每个问题都标注了预期的路由类型和子决策路径

---

## 1. General-Query 测试（打招呼/闲聊）

### 1.1 基本问候
**问题**: `你好`
- **预期路由**: `general-query`
- **预期节点**: `respond_to_general_query`
- **预期行为**: 使用礼貌用语回复，带有"亲～"或"厨友您好～"

### 1.2 礼貌寒暄
**问题**: `早上好`
- **预期路由**: `general-query`
- **预期节点**: `respond_to_general_query`
- **预期行为**: 温暖回应，可能带 emoji

### 1.3 感谢反馈
**问题**: `谢谢你的帮助`
- **预期路由**: `general-query`
- **预期节点**: `respond_to_general_query`
- **预期行为**: 表达感谢和继续服务意愿

### 1.4 情绪表达
**问题**: `今天心情不错`
- **预期路由**: `general-query`
- **预期节点**: `respond_to_general_query`
- **预期行为**: 积极回应，引导菜谱话题

---

## 2. Additional-Query 测试（补充信息）

### 2.1 模糊提问
**问题**: `我想做菜`
- **预期路由**: `additional-query`
- **预期节点**: `get_additional_info`
- **预期行为**:
  - 先通过 guardrails 检查（通过）
  - 友好询问具体菜名或菜系

### 2.2 缺少关键信息
**问题**: `这个菜怎么做好吃`
- **预期路由**: `additional-query`
- **预期节点**: `get_additional_info`
- **预期行为**: 询问"哪道菜"

### 2.3 营养问题（缺份量）
**问题**: `这个菜热量高吗`
- **预期路由**: `additional-query`
- **预期节点**: `get_additional_info`
- **预期行为**: 询问具体菜名或份量

### 2.4 烹饪失败（描述不清）
**问题**: `我做的菜不好吃`
- **预期路由**: `additional-query`
- **预期节点**: `get_additional_info`
- **预期行为**: 询问具体是什么菜、失败的表现

---

## 3. KB-Query 测试（向量知识库检索）

### 3.1 菜谱历史典故
**问题**: `宫保鸡丁的历史典故是什么`
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期子流程**:
  - 调用 `create_kb_multi_tool_workflow`
  - 智能决策选择 Milvus 或 PostgreSQL（pgvector）
  - 可能触发外部检索（如配置允许）
  - Finalizer 汇总结果
- **预期行为**: 返回历史背景、文化渊源

### 3.2 菜品背景文化
**问题**: `佛跳墙这道菜的由来`
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期子决策**:
  - 路由器选择 Milvus 或 pgvector
  - 根据相似度阈值决定是否补充外部检索
- **预期行为**: 返回菜品背景、传说故事

### 3.3 地域流派介绍
**问题**: `川菜的特点是什么`
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期子决策**:
  - Multi-tool workflow 智能选择向量检索源
  - 合并多个来源（Milvus + pgvector）
- **预期行为**: 返回流派特征、代表菜品

### 3.4 名厨偏好介绍
**问题**: `川菜大师有哪些`
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期行为**: 返回名厨信息、烹饪风格

### 3.5 食材营养科普
**问题**: `西兰花有什么营养价值`
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期子决策**:
  - 可能同时查询 Milvus 和 pgvector
  - Reranker 重排序结果
- **预期行为**: 返回营养成分、健康功效

---

## 4. GraphRAG-Query 测试（图谱推理 + 多工具决策）

这是最复杂的路由，进入后会根据问题类型智能决策使用以下工具：
- **cypher_query**: 动态生成 Cypher 查询（Neo4j）
- **predefined_cypher**: 使用预定义 Cypher 模板
- **microsoft_graphrag_query**: 使用 GraphRAG（LightRAG）
- **text2sql_query**: 查询结构化数据库（MySQL）

### 4.1 菜谱做法步骤（→ Cypher）
**问题**: `红烧肉怎么做`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - Planner 节点分析问题
  - 路由选择 `cypher_query` 或 `predefined_cypher`
  - 查询 Neo4j: `(Dish)-[:HAS_STEP]->(CookingStep)`
  - Finalizer 汇总烹饪步骤
- **预期行为**: 返回分步骤的详细做法

### 4.2 食材用量查询（→ Cypher）
**问题**: `宫保鸡丁需要哪些食材`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - 选择 `predefined_cypher`（已有模板）
  - 查询: `(Dish)-[:HAS_MAIN_INGREDIENT|HAS_AUX_INGREDIENT]->(Ingredient)`
- **预期行为**: 返回主料、辅料清单

### 4.3 烹饪技巧细节（→ Cypher + GraphRAG）
**问题**: `炒青菜怎么保持翠绿`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - 可能同时调用 `cypher_query`（查询烹饪方法节点）
  - 和 `microsoft_graphrag_query`（推理相关技巧）
  - Finalizer 融合两种来源
- **预期行为**: 返回火候、时间、技巧

### 4.4 火候判断（→ GraphRAG）
**问题**: `怎么判断鱼熟了`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - 优先选择 `microsoft_graphrag_query`（需要推理）
  - LightRAG 图推理
- **预期行为**: 返回判断技巧、经验分享

### 4.5 失败排查（→ GraphRAG + Cypher）
**问题**: `为什么我做的红烧肉发柴`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - 先用 `cypher_query` 查询正确做法
  - 再用 `microsoft_graphrag_query` 推理可能原因
  - Finalizer 对比分析
- **预期行为**: 返回可能原因和改进建议

### 4.6 综合图谱推理（→ Multiple Tools）
**问题**: `什么菜适合感冒的人吃`
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - `cypher_query`: 查询 `(Dish)-[:HAS_HEALTH_BENEFIT]->(HealthBenefit)`
  - `microsoft_graphrag_query`: 推理食疗组合
  - Finalizer 汇总多源信息
- **预期行为**: 返回推荐菜品、食疗理由

---

## 5. Text2SQL-Query 测试（结构化数据查询）

### 5.1 数据统计（→ Text2SQL）
**问题**: `数据库里有多少道菜`
- **预期路由**: `graphrag-query` 或 `text2sql-query`（启发式关键词"多少"）
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - Planner 识别为统计查询
  - 路由到 `text2sql_query` 工具
  - 生成 SQL: `SELECT COUNT(*) FROM recipes`
  - 执行 MySQL 查询
- **预期行为**: 返回具体数字

### 5.2 数据排名（→ Text2SQL）
**问题**: `哪个菜系的菜谱最多`
- **预期路由**: `text2sql-query`（启发式关键词"最多"）
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - `text2sql_query` 工具
  - SQL: `SELECT category, COUNT(*) FROM recipes GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1`
- **预期行为**: 返回菜系名称和数量

### 5.3 数据趋势分析（→ Text2SQL）
**问题**: `统计每个口味的菜谱数量`
- **预期路由**: `text2sql-query`（启发式关键词"统计"）
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - `text2sql_query` 工具
  - 生成 GROUP BY 查询
- **预期行为**: 返回分类统计表

### 5.4 混合查询（→ Text2SQL + Cypher）
**问题**: `麻辣口味的菜有多少道`
- **预期路由**: `graphrag-query`（需要图谱 + 统计）
- **预期节点**: `create_research_plan`
- **预期子决策**:
  - 可能同时调用 `cypher_query`（查询 Flavor 节点）
  - 和 `text2sql_query`（统计数量）
  - Finalizer 合并结果
- **预期行为**: 返回数量 + 示例菜品

---

## 6. Image-Query 测试（图片识别/生成）

### 6.1 图片识别
**问题**: `这是什么菜`（附带图片路径）
- **预期路由**: `image-query`（或被 `route_query` 中的 `config.image_path` 拦截）
- **预期节点**: `create_image_query`
- **预期行为**:
  - 调用 Vision API 识别图片
  - 返回菜名、食材、烹饪方法推测

### 6.2 图片生成
**问题**: `生成一张红烧肉的图片`
- **预期路由**: `image-query`
- **预期节点**: `create_image_query`
- **预期子决策**:
  - 检测生成关键词（"生成"）
  - 调用 `_generate_image` 函数
  - LLM 优化提示词（`IMAGE_GENERATION_ENHANCE_PROMPT`）
  - CogView-4 API 生成
- **预期行为**: 返回图片 URL 和成功提示

---

## 7. File-Query 测试（文件上传）

### 7.1 文本文件导入
**问题**: `帮我分析这个菜谱文件`（附带 .txt 文件路径）
- **预期路由**: `file-query`（或被 `route_query` 中的 `config.file_path` 拦截）
- **预期节点**: `create_file_query`
- **预期行为**:
  - 读取文件内容
  - 导入知识库（Milvus/pgvector）
  - 调用 `create_knowledge_query_node` 回答问题

### 7.2 Excel 导入（需要外部服务）
**问题**: `导入这个菜谱 Excel`（附带 .xlsx 文件路径）
- **预期路由**: `file-query`
- **预期节点**: `create_file_query`
- **预期子决策**:
  - 检测 Excel 格式
  - 调用外部 Ingest Service API
- **预期行为**: 返回导入成功提示

---

## 8. 边界测试（Guardrails 安全拦截）

### 8.1 无关问题（应被拒绝）
**问题**: `今天天气怎么样`
- **预期路由**: `additional-query` 或 `general-query`
- **预期节点**: `get_additional_info` → guardrails 检查
- **预期行为**:
  - Guardrails 返回 `end`
  - 输出礼貌拒绝："这个问题不太属于我们的菜谱范围呢"

### 8.2 政治敏感话题（应被拒绝）
**问题**: `你怎么看待某某政治人物`
- **预期路由**: `general-query`
- **预期节点**: `respond_to_general_query`
- **预期行为**: 礼貌拒绝，引导回菜谱话题

### 8.3 医疗诊断（应被拒绝）
**问题**: `我肚子疼应该吃什么药`
- **预期路由**: `additional-query`
- **预期节点**: `get_additional_info` → guardrails 检查
- **预期行为**:
  - Guardrails 拦截
  - 建议咨询医生，可提供食疗建议（边界）

---

## 9. Fallback 测试（降级和兜底）

### 9.1 LLM 路由失败
**问题**: （构造一个让 LLM 返回无效类型的问题）
- **预期行为**:
  - `_heuristic_router` 启发式兜底
  - 如果启发式也失败，默认 `kb-query`

### 9.2 Multi-tool Workflow 异常
**问题**: `宫保鸡丁怎么做`（但 Neo4j 连接失败）
- **预期路由**: `graphrag-query`
- **预期节点**: `create_research_plan`
- **预期行为**:
  - 捕获异常
  - 降级到 KB 向量检索
  - 返回部分结果或提示"暂时无法访问图谱"

### 9.3 KB Multi-tool 降级
**问题**: `川菜的历史`（但 Multi-tool workflow 初始化失败）
- **预期路由**: `kb-query`
- **预期节点**: `create_kb_query`
- **预期行为**:
  - 捕获 `create_kb_multi_tool_workflow` 异常
  - 降级到直接 `create_knowledge_query_node`
  - 返回单一向量检索结果

---

## 10. 混合场景测试（多轮对话）

### 10.1 问候 → 菜谱查询
```
用户: 你好
    预期: general-query → 礼貌回复
用户: 我想做宫保鸡丁
    预期: graphrag-query → 返回做法
```

### 10.2 模糊 → 补充 → 执行
```
用户: 这个菜怎么做
    预期: additional-query → 询问哪道菜
用户: 红烧肉
    预期: graphrag-query → 返回红烧肉做法
```

### 10.3 知识库 → 图谱推理
```
用户: 川菜有什么特点
    预期: kb-query → 返回川菜特点
用户: 推荐几道川菜
    预期: graphrag-query → 查询图谱推荐
```

---

## 测试执行建议

### 1. 日志观察要点
在 `gustobot/application/agents/lg_builder.py` 和相关子模块中观察以下日志：
- `analyze_and_route_query` 的路由结果
- `route_query` 的条件分支
- Multi-tool workflow 的工具选择日志
- KB Multi-tool 的 Milvus/pgvector 决策
- Text2SQL 的 SQL 生成日志
- Guardrails 的 `decision` 结果

### 2. 预期输出格式
每个问题应该在日志中看到：
```
INFO - -----Analyze user query type-----
INFO - Analyze user query type completed, result: {'type': 'graphrag-query', 'logic': '...', 'question': '...'}
INFO - ------execute local knowledge base query------
INFO - Multi-tool workflow selected tools: ['cypher_query', 'predefined_cypher']
INFO - Finalizer combining results from 2 sources
```

### 3. 验证 KB Multi-tool 智能决策
对于 `kb-query` 类型，特别关注：
```python
# 在 create_kb_multi_tool_workflow 中应该看到：
INFO - Router selected tools: ['milvus', 'pgvector']
INFO - Milvus retrieval returned 5 results
INFO - PostgreSQL pgvector returned 3 results
INFO - Reranker merged and reranked 8 results to top 5
```

### 4. 验证 GraphRAG Multi-tool 智能决策
对于 `graphrag-query` 类型，特别关注：
```python
# 在 create_multi_tool_workflow 中应该看到：
INFO - Planner analyzed question and selected tools: ['cypher_query', 'microsoft_graphrag_query']
INFO - Executing cypher_query with question: ...
INFO - Executing microsoft_graphrag_query with question: ...
INFO - Finalizer combining 2 tool results
```

---

## 预期成功标准

✅ **General-Query**: 所有问候/闲聊问题正确识别，无误入其他路由
✅ **Additional-Query**: 模糊问题触发补充询问，Guardrails 正确拦截无关问题
✅ **KB-Query**: 历史文化类问题正确路由，Multi-tool 智能选择 Milvus/pgvector
✅ **GraphRAG-Query**: 做法/技巧类问题正确路由，Planner 智能选择 Cypher/GraphRAG/Text2SQL
✅ **Text2SQL-Query**: 统计类问题正确识别（启发式或 LLM），生成有效 SQL
✅ **Image/File-Query**: 配置路径正确拦截，调用对应 API
✅ **Fallback**: 异常情况触发降级逻辑，不崩溃

---

## 附录：测试脚本模板

```python
import asyncio
from gustobot.application.agents.lg_builder import graph
from langchain_core.messages import HumanMessage

async def test_routing(question: str, image_path: str = None, file_path: str = None):
    config = {
        "configurable": {
            "thread_id": "test_session_001",
            "image_path": image_path,
            "file_path": file_path,
        }
    }

    input_state = {
        "messages": [HumanMessage(content=question)]
    }

    result = await graph.ainvoke(input_state, config=config)
    print(f"\n问题: {question}")
    print(f"路由: {result.get('router', {}).get('type')}")
    print(f"回复: {result['messages'][-1].content[:100]}...")
    return result

# 运行测试
async def run_all_tests():
    # 1. General-Query
    await test_routing("你好")
    await test_routing("谢谢")

    # 2. Additional-Query
    await test_routing("我想做菜")
    await test_routing("这个菜怎么做")

    # 3. KB-Query
    await test_routing("宫保鸡丁的历史典故是什么")
    await test_routing("川菜的特点是什么")

    # 4. GraphRAG-Query (Cypher)
    await test_routing("红烧肉怎么做")
    await test_routing("宫保鸡丁需要哪些食材")

    # 5. GraphRAG-Query (GraphRAG)
    await test_routing("怎么判断鱼熟了")
    await test_routing("炒青菜怎么保持翠绿")

    # 6. Text2SQL-Query
    await test_routing("数据库里有多少道菜")
    await test_routing("哪个菜系的菜谱最多")

    # 7. Image-Query
    await test_routing("生成一张红烧肉的图片")

    # 8. Guardrails
    await test_routing("今天天气怎么样")

asyncio.run(run_all_tests())
```

---

**测试执行**: 将问题逐个或批量输入到 GustoBot API，观察日志输出和返回结果，对比预期行为。

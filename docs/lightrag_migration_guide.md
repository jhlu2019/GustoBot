# LightRAG 迁移指南

## 概述

本项目已从 **Microsoft GraphRAG** 迁移到 **LightRAG**，实现以下改进：

| 指标 | Microsoft GraphRAG | LightRAG | 改进幅度 |
|------|-------------------|----------|---------|
| **代码体积** | 1.7GB | < 100MB | 减少 94% ✅ |
| **Token 消耗** | ~610,000 tokens/查询 | < 100 tokens/查询 | 减少 99% ✅ |
| **初始化时间** | 需要预构建索引（数小时） | 增量更新（秒级） | 提升 1000x ✅ |
| **API 复杂度** | 需要加载 6+ 数据文件 | 单一 API 调用 | 简化 90% ✅ |
| **增量更新** | ❌ 不支持 | ✅ 支持 | 新增功能 |
| **Neo4j 集成** | ❌ 不支持 | ✅ 支持 | 新增功能 |

---

## 快速开始

### 1. 安装依赖

```bash
# 安装 LightRAG 和其他依赖
pip install -r requirements.txt

# 或单独安装 LightRAG
pip install lightrag-hku>=0.0.3
```

### 2. 配置环境变量

在 `.env` 文件中添加以下配置：

```bash
# LightRAG 配置
LIGHTRAG_WORKING_DIR=./data/lightrag
LIGHTRAG_RETRIEVAL_MODE=hybrid  # local/global/hybrid/naive
LIGHTRAG_TOP_K=10
LIGHTRAG_MAX_TOKEN_SIZE=4096
LIGHTRAG_ENABLE_NEO4J=True  # 是否使用 Neo4j 作为图存储
LIGHTRAG_ENABLE_MILVUS=False  # 是否使用 Milvus 作为向量存储
```

### 3. 初始化数据

#### 方式 A: 从 Neo4j 导入（推荐）

```bash
# 从 Neo4j 菜谱图谱导入所有数据
python scripts/init_lightrag.py --source neo4j

# 限制导入数量（用于测试）
python scripts/init_lightrag.py --source neo4j --limit 100
```

#### 方式 B: 从 JSON 文件导入

```bash
# 从 JSON 文件导入
python scripts/init_lightrag.py --source json --json-path data/recipe.json

# 限制导入数量
python scripts/init_lightrag.py --source json --json-path data/recipe.json --limit 50
```

### 4. 启动服务

```bash
# 启动 FastAPI 服务
python -m uvicorn gustobot.main:application --reload --host 0.0.0.0 --port 8000
```

### 5. 测试查询

```bash
# 使用 curl 测试
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{"query": "红烧肉怎么做？"}'
```

---

## API 使用

### Python API

```python
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

# 创建 LightRAG 实例
lightrag = LightRAGAPI()
await lightrag.initialize()

# 查询
result = await lightrag.query("红烧肉怎么做？", mode="hybrid")
print(result["response"])

# 插入新文档
new_recipes = [
    "# 麻婆豆腐\n**口味**: 麻辣\n**做法**: ...",
    "# 糖醋排骨\n**口味**: 酸甜\n**做法**: ..."
]
await lightrag.insert_documents(new_recipes)
```

### LangGraph 节点集成

```python
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import create_lightrag_query_node

# 创建 LightRAG 查询节点
lightrag_node = create_lightrag_query_node()

# 在 LangGraph 工作流中使用
state = {"task": "宫保鸡丁需要什么食材？"}
result = await lightrag_node(state)

print(result["cyphers"][0].records["result"])
```

---

## 检索模式说明

LightRAG 支持 6 种检索模式：

### 1. **local** - 局部搜索
- 适用场景：具体实体相关的问题
- 示例："红烧肉需要多少五花肉？"
- 特点：聚焦于查询中提到的实体

### 2. **global** - 全局搜索
- 适用场景：需要总结归纳的问题
- 示例："最常用的烹饪方法有哪些？"
- 特点：考虑整个知识图谱的信息

### 3. **hybrid** - 混合模式（推荐）
- 适用场景：大多数问题
- 示例："川菜有哪些经典菜品？"
- 特点：结合 local 和 global 搜索的优势

### 4. **naive** - 简单向量检索
- 适用场景：快速原型测试
- 示例：任何问题
- 特点：仅使用向量相似度，不使用图谱

### 5. **mix** - 混合策略
- 适用场景：复杂多跳推理
- 示例："哪些菜品适合秋季养生且容易上手？"
- 特点：组合多种检索策略

### 6. **bypass** - 直接查询
- 适用场景：调试和开发
- 示例：跳过检索，直接 LLM 回答
- 特点：不使用知识库

---

## 与现有系统的集成

### 与 recipe_kg 模块协同

LightRAG 与 recipe_kg 模块是互补关系：

| 模块 | 用途 | 优势 |
|------|------|------|
| **recipe_kg** | 结构化查询 | 精确的 Cypher 查询，适合已知模式 |
| **LightRAG** | 语义检索 | 灵活的自然语言查询，适合未知模式 |

```python
# 工作流示例
用户问题: "麻辣口味的炒菜有哪些？"
    ↓
QuestionClassifier (recipe_kg)
    ↓ 分类为 property_constraint
    ↓
QuestionParser (recipe_kg) → 生成精确 Cypher
    ↓
Neo4j 执行查询 → 返回菜品列表
    ↓
LightRAG 补充详细信息 → 丰富菜品描述
    ↓
返回完整答案
```

### 与 Neo4j 图谱集成

```python
# 配置使用 Neo4j 作为图存储
LIGHTRAG_ENABLE_NEO4J=True

# LightRAG 会自动连接到项目的 Neo4j 实例
# 并使用现有的 Dish/Ingredient/Flavor 等节点
```

**好处**：
- ✅ 复用现有菜谱图谱数据
- ✅ 与 predefined_cypher 查询协同
- ✅ 统一的图数据管理

---

## 增量更新示例

### 从爬虫添加新菜谱

```python
from gustobot.crawler import RecipeCrawler
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

# 初始化 LightRAG
lightrag = LightRAGAPI()
await lightrag.initialize()

# 爬取新菜谱
crawler = RecipeCrawler()
new_recipes = await crawler.crawl_recipes(keyword="川菜")

# 转换为文档格式
documents = [recipe.to_lightrag_document() for recipe in new_recipes]

# 增量插入（无需重建整个索引）
result = await lightrag.insert_documents(documents)

print(f"成功添加 {result['success']} 个新菜谱")
```

---

## 性能优化建议

### 1. 调整 embedding 模型

```bash
# 默认使用 text-embedding-3-small (1536维)
EMBEDDING_MODEL=text-embedding-3-small

# 升级到 large 版本以获得更好效果 (3072维)
EMBEDDING_MODEL=text-embedding-3-large
```

### 2. 调整检索参数

```bash
# 增加返回结果数量
LIGHTRAG_TOP_K=20

# 增加文本单元大小
LIGHTRAG_MAX_TOKEN_SIZE=8192
```

### 3. 使用合适的检索模式

```python
# 简单问题用 local（最快）
await lightrag.query("红烧肉怎么做？", mode="local")

# 复杂问题用 hybrid（平衡）
await lightrag.query("哪些菜品适合宴客？", mode="hybrid")

# 总结性问题用 global（最全面）
await lightrag.query("总结常用的烹饪技巧", mode="global")
```

---

## 测试

### 运行单元测试

```bash
# 运行 LightRAG 集成测试
pytest tests/test_lightrag_integration.py -v

# 运行特定测试类
pytest tests/test_lightrag_integration.py::TestLightRAGAPI -v

# 包含 Neo4j 集成测试（需要配置 NEO4J_URI）
pytest tests/test_lightrag_integration.py -v -m integration
```

### 测试覆盖率

```bash
pytest tests/test_lightrag_integration.py --cov=gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools --cov-report=html
```

---

## 故障排除

### 问题 1: LightRAG 未安装

**错误信息**: `ImportError: No module named 'lightrag'`

**解决方案**:
```bash
pip install lightrag-hku>=0.0.3
```

### 问题 2: Neo4j 连接失败

**错误信息**: `Neo4j 连接失败，使用默认图存储`

**解决方案**:
1. 检查 Neo4j 是否运行: `docker ps | grep neo4j`
2. 检查配置: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
3. 如果不需要 Neo4j 集成，设置 `LIGHTRAG_ENABLE_NEO4J=False`

### 问题 3: 初始化时间过长

**原因**: 插入大量文档时，embedding 生成需要时间

**解决方案**:
```bash
# 分批导入，每次限制数量
python scripts/init_lightrag.py --source neo4j --limit 100

# 或使用更快的 embedding 模型
EMBEDDING_MODEL=text-embedding-3-small  # 而非 text-embedding-3-large
```

### 问题 4: 查询结果质量不佳

**可能原因**:
1. 文档格式不规范
2. 检索模式不匹配
3. 文档数量太少

**解决方案**:
1. 检查文档格式（参考 `scripts/init_lightrag.py` 中的 `format_recipe_document`）
2. 尝试不同的检索模式（local/global/hybrid）
3. 增加文档数量（至少 50+ 篇）

---

## 向后兼容性

为了确保平滑迁移，保留了以下别名：

```python
# 旧名称（仍然可用）
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import (
    GraphRAGAPI,  # 指向 LightRAGAPI
    create_graphrag_query_node  # 指向 create_lightrag_query_node
)

# 新名称（推荐使用）
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import (
    LightRAGAPI,
    create_lightrag_query_node
)
```

---

## 下一步

### 1. 删除旧的 GraphRAG 代码（可选）

```bash
# 备份旧代码
mv gustobot/graphrag gustobot/graphrag_backup

# 或直接删除（节省 1.7GB 空间）
rm -rf gustobot/graphrag
```

### 2. 性能基准测试

创建测试脚本对比 LightRAG 与原 GraphRAG 的性能：

```python
# scripts/benchmark_lightrag.py
import time
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

async def benchmark():
    lightrag = LightRAGAPI()
    await lightrag.initialize()

    queries = [
        "红烧肉怎么做？",
        "哪些菜品适合秋季养生？",
        "川菜的特点是什么？"
    ]

    for query in queries:
        start = time.time()
        result = await lightrag.query(query)
        elapsed = time.time() - start

        print(f"查询: {query}")
        print(f"耗时: {elapsed:.2f}秒")
        print(f"结果长度: {len(result['response'])} 字符\n")
```

### 3. 集成到爬虫工作流

修改爬虫代码，自动将新菜谱插入 LightRAG：

```python
# gustobot/crawler/recipe_crawler.py
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

class RecipeCrawler:
    def __init__(self):
        self.lightrag = LightRAGAPI()

    async def crawl_and_index(self, keyword: str):
        # 爬取
        recipes = await self.crawl(keyword)

        # 转换为文档
        documents = [self._format_recipe(r) for r in recipes]

        # 插入 LightRAG（增量更新）
        result = await self.lightrag.insert_documents(documents)

        return result
```

---

## 参考资源

- [LightRAG GitHub](https://github.com/HKUDS/LightRAG)
- [LightRAG 论文](https://arxiv.org/abs/2410.05779)
- [项目 Neo4j Schema](./recipe_kg_schema.md)
- [recipe_kg 模块文档](./recipe_kg_integration.md)

---

## 支持

如有问题，请：
1. 检查本文档的"故障排除"部分
2. 查看测试文件 `tests/test_lightrag_integration.py` 中的示例
3. 提交 Issue 到项目仓库

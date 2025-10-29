# LightRAG 数据初始化指南

## 📊 数据来源

LightRAG 的初始化数据来自以下两个主要来源：

### 1. **Neo4j 知识图谱** (推荐)
- **位置**: Neo4j 数据库
- **内容**: 结构化的菜谱知识图谱
- **节点类型**:
  - `Dish` (菜品)
  - `Ingredient` (食材)
  - `Flavor` (口味)
  - `CookingMethod` (烹饪方法)
  - `DishType` (菜品类型)
- **优势**: 数据结构化，关系清晰，查询高效

### 2. **JSON 文件**
- **位置**: `data/recipe.json` (24MB, ~数千条菜谱)
- **内容**: 原始菜谱数据
- **格式**:
```json
{
  "菜品名称": {
    "name": "红烧肉",
    "category": "家常菜",
    "ingredients": ["五花肉500g", "冰糖30g"],
    "instructions": "制作步骤...",
    "flavors": ["咸", "鲜"],
    "methods": ["红烧"],
    "cook_time": "1小时"
  }
}
```

---

## 🚀 初始化方法

### 方法 1: 从 Neo4j 导入 (推荐)

**前提条件**:
- Neo4j 已启动且包含菜谱数据
- 配置正确（见下方配置部分）

**命令**:
```bash
# 完整导入
python scripts/init_lightrag.py --source neo4j

# 测试导入（限制 10 条）
python scripts/init_lightrag.py --source neo4j --limit 10

# 指定工作目录
python scripts/init_lightrag.py --source neo4j --working-dir ./my_lightrag_data
```

**导入流程**:
1. 连接 Neo4j 数据库
2. 执行 Cypher 查询获取菜品及关联数据
3. 格式化为文本文档
4. 批量插入 LightRAG

**示例输出**:
```
INFO: 初始化 LightRAG
INFO: 开始从 Neo4j 导入菜谱数据
INFO: 执行 Neo4j 查询
INFO: 已准备 10 个文档
INFO: 已准备 20 个文档
...
INFO: 共准备了 100 个菜谱文档
INFO: 开始插入文档到 LightRAG
INFO: 开始插入 100 个文档
INFO: 已插入 10/100 个文档
...
INFO: 文档插入完成，成功: 100，失败: 0
INFO: 导入完成: 总数=100, 成功=100, 失败=0
INFO: ✅ LightRAG 初始化完成！成功导入 100 个菜谱文档
INFO: 📂 工作目录: ./data/lightrag
INFO: 🔍 检索模式: hybrid
```

---

### 方法 2: 从 JSON 文件导入

**前提条件**:
- `data/recipe.json` 文件存在

**命令**:
```bash
# 使用默认 JSON 文件
python scripts/init_lightrag.py --source json

# 指定 JSON 文件
python scripts/init_lightrag.py --source json --json-path /path/to/recipes.json

# 测试导入（限制 10 条）
python scripts/init_lightrag.py --source json --limit 10
```

---

## ⚙️ 配置

### 环境变量配置 (.env)

```bash
# LightRAG 配置
LIGHTRAG_WORKING_DIR=./data/lightrag
LIGHTRAG_RETRIEVAL_MODE=hybrid  # local, global, hybrid, naive, mix, bypass
LIGHTRAG_TOP_K=10
LIGHTRAG_MAX_TOKEN_SIZE=4096
LIGHTRAG_ENABLE_NEO4J=true  # 是否使用 Neo4j 作为图存储

# OpenAI 配置
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Neo4j 配置（如果启用）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### Settings 配置 (gustobot/config/settings.py)

```python
# LightRAG configuration
LIGHTRAG_WORKING_DIR: str = "./data/lightrag"
LIGHTRAG_RETRIEVAL_MODE: str = "hybrid"
LIGHTRAG_TOP_K: int = 10
LIGHTRAG_MAX_TOKEN_SIZE: int = 4096
LIGHTRAG_ENABLE_NEO4J: bool = True

# Neo4j configuration
NEO4J_URI: str = "bolt://neo4j:7687"
NEO4J_USER: Optional[str] = None
NEO4J_PASSWORD: Optional[str] = None
NEO4J_DATABASE: str = "neo4j"
NEO4J_RECIPE_JSON_PATH: str = "data/recipe.json"
```

---

## 📁 生成的文件结构

初始化后，LightRAG 会在工作目录生成以下文件：

```
data/lightrag/
├── graph_chunk_entity_relation.graphml  # 知识图谱（NetworkX 格式）
├── kv_store_doc_status.json             # 文档处理状态
├── kv_store_full_docs.json              # 完整文档存储
├── kv_store_text_chunks.json            # 文本块存储
├── vdb_chunks.json                      # 文本块向量索引
├── vdb_entities.json                    # 实体向量索引
└── vdb_relationships.json               # 关系向量索引
```

**如果启用 Neo4j**:
- 图谱数据存储在 Neo4j 数据库
- 不生成 `graph_chunk_entity_relation.graphml` 文件

---

## 🔍 文档格式

LightRAG 中存储的菜谱文档格式示例：

```markdown
# 红烧肉

**口味**: 咸, 鲜
**烹饪方法**: 红烧
**菜品类型**: 家常菜, 热菜
**烹饪时长**: 1小时

**食材**:
- 五花肉: 500g
- 冰糖: 30g
- 生抽: 2勺
- 老抽: 1勺
- 料酒: 2勺
- 八角: 2个
- 桂皮: 1小块

**做法**:
1. 五花肉切成2cm见方的块状
2. 冷水下锅，焯水去血沫
3. 锅中放少许油，放入冰糖炒糖色
4. 加入五花肉翻炒上色
5. 加入生抽、老抽、料酒调味
6. 加入八角、桂皮等香料
7. 加水没过肉，大火烧开后转小火炖1小时
8. 大火收汁即可
```

---

## 🧪 验证初始化

### 1. 检查文件是否生成

```bash
ls -lh data/lightrag/
```

应该看到上述文件列表。

### 2. 测试查询

```python
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

async def test_query():
    api = LightRAGAPI()
    result = await api.query("红烧肉怎么做？", mode="hybrid")
    print(result["response"])

# 运行测试
import asyncio
asyncio.run(test_query())
```

### 3. 查看统计信息

```bash
# 查看文件大小
du -sh data/lightrag/

# 查看文档数量
python -c "
import json
with open('data/lightrag/kv_store_doc_status.json', 'r') as f:
    data = json.load(f)
    print(f'文档总数: {len(data)}')
"
```

---

## 🔄 更新数据

### 增量更新

LightRAG 支持增量插入：

```python
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

async def add_new_recipe():
    api = LightRAGAPI()

    new_recipe = """
    # 宫保鸡丁

    **口味**: 麻, 辣
    **烹饪方法**: 炒

    **食材**:
    - 鸡胸肉: 300g
    - 花生米: 50g
    - 干辣椒: 10个

    **做法**:
    1. 鸡胸肉切丁，腌制15分钟
    2. 热油炒花生米至金黄
    3. 炒鸡丁至变色
    4. 加入干辣椒和调料翻炒
    5. 最后加入花生米即可
    """

    result = await api.insert_documents([new_recipe])
    print(f"插入结果: {result}")
```

### 完全重建

如果需要完全重建索引：

```bash
# 删除旧数据
rm -rf data/lightrag/*

# 重新初始化
python scripts/init_lightrag.py --source neo4j
```

---

## 🎯 最佳实践

1. **初次使用**:
   - 先用 `--limit 10` 测试，确保配置正确
   - 验证生成的文档格式符合预期
   - 然后再导入完整数据

2. **数据源选择**:
   - **开发/测试**: 使用 JSON 文件（简单快速）
   - **生产环境**: 使用 Neo4j（数据结构化，可实时更新）

3. **存储选择**:
   - **小规模数据** (< 1000 文档): 使用默认 NetworkX 存储
   - **大规模数据** (> 1000 文档): 启用 Neo4j 图存储

4. **性能优化**:
   - 批量插入时调整 batch_size（默认 10）
   - 对于大量数据，可以分批次导入
   - 启用 Neo4j 可显著提升大规模数据性能

---

## ❓ 常见问题

### Q1: 初始化失败，提示 Neo4j 连接错误

**A**: 检查 Neo4j 是否启动，配置是否正确：
```bash
# 检查 Neo4j 状态
docker ps | grep neo4j

# 测试连接
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('Neo4j 连接成功')
"
```

### Q2: 文档插入失败

**A**: 检查 OpenAI API 配置：
```bash
# 测试 API
python -c "
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'test'}]
)
print('OpenAI API 正常')
"
```

### Q3: 查询结果不准确

**A**: 尝试不同的检索模式：
- `naive`: 简单向量检索
- `local`: 局部上下文检索
- `global`: 全局知识检索
- `hybrid`: 混合检索（推荐）

---

## 📚 相关文档

- [LIGHTRAG_FIXES.md](./LIGHTRAG_FIXES.md) - LightRAG 代码修复说明
- [FINAL_VERIFICATION.md](./FINAL_VERIFICATION.md) - 最终验证清单
- [scripts/init_lightrag.py](./scripts/init_lightrag.py) - 初始化脚本源码

---

## 🎉 总结

**数据来源**:
- ✅ Neo4j 知识图谱 (推荐)
- ✅ JSON 文件 (`data/recipe.json`)

**初始化命令**:
```bash
# 从 Neo4j 导入
python scripts/init_lightrag.py --source neo4j

# 从 JSON 导入
python scripts/init_lightrag.py --source json

# 测试（限制 10 条）
python scripts/init_lightrag.py --source neo4j --limit 10
```

**存储位置**: `./data/lightrag/`

现在你知道 LightRAG 的数据从哪里来以及如何初始化了！🚀

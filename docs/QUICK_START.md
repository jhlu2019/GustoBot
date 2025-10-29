# GustoBot 快速启动指南

## 🚀 快速开始

### 1. 启动所有服务

```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f server
```

服务端口：
- **FastAPI Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:17474
- **MySQL**: localhost:13306
- **Redis**: localhost:6379
- **Milvus**: localhost:19530

---

## 🧪 测试检索流程

### 测试 1: 配置验证

```bash
python3 -c "
from gustobot.config.settings import settings
print('Embedding:', settings.EMBEDDING_MODEL, '@', settings.EMBEDDING_BASE_URL)
print('Reranker:', settings.RERANK_MODEL, '@', settings.RERANK_BASE_URL)
print('Recall:', settings.RERANK_MAX_CANDIDATES, '→ Return:', settings.RERANK_TOP_N)
"
```

**预期输出**:
```
Embedding: bge-m3 @ http://10.168.2.250:9997/v1
Reranker: bge-reranker-large @ http://10.168.2.250:9997/v1
Recall: 20 → Return: 6
```

---

### 测试 2: 知识库检索

```bash
# 使用 curl 测试知识检索接口
curl -X POST "http://localhost:8000/api/v1/knowledge/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "红烧肉怎么做？需要什么食材？",
    "top_k": 6
  }' | jq
```

**预期响应**:
```json
{
  "results": [
    {
      "content": "菜名：红烧肉\n食材：五花肉500g、冰糖30g...",
      "score": 0.95,
      "rerank_score": 0.98,
      "metadata": {
        "recipe_id": "...",
        "name": "红烧肉",
        "category": "家常菜"
      }
    }
  ],
  "total": 6
}
```

**日志输出** (server logs):
```
[INFO] Embedding query using bge-m3
[INFO] Milvus search: recall_k=20
[INFO] Reranker enabled: custom @ http://10.168.2.250:9997/v1
[INFO] Reranked 20 docs → Top 6
```

---

### 测试 3: 对话接口

```bash
# 测试多轮对话（包含语义缓存）
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "session_id": "session_001",
    "query": "红烧肉怎么做？"
  }' | jq

# 第二次相同问题（应该命中缓存）
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "session_id": "session_001",
    "query": "红烧肉怎么做？"
  }' | jq
```

**预期响应**:
```json
{
  "answer": "红烧肉的做法如下：...",
  "route": "knowledge",
  "confidence": 0.95,
  "cached": false,  // 第一次
  "sources": [
    {"name": "红烧肉", "score": 0.98}
  ]
}
```

第二次请求应该返回 `"cached": true` 且响应更快。

---

## 📊 检索工作流详解

### 完整流程

```
用户查询: "红烧肉怎么做？"
    │
    ▼
┌─────────────────────────────────────────────┐
│ Step 1: Embedding 向量化                     │
│ ─────────────────────────────────────────── │
│ API: http://10.168.2.250:9997/v1/embeddings │
│ Model: bge-m3                               │
│ Input: "红烧肉怎么做？"                       │
│ Output: [0.023, -0.145, ..., 0.089] (1024维)│
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Step 2: Milvus 向量召回                      │
│ ─────────────────────────────────────────── │
│ Collection: recipes                         │
│ Query Vector: 1024-dim                      │
│ Top K: 20 (RERANK_MAX_CANDIDATES)           │
│ Results: 20个相关菜谱文档                    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Step 3: Reranker 精排                        │
│ ─────────────────────────────────────────── │
│ API: http://10.168.2.250:9997/v1/rerank     │
│ Model: bge-reranker-large                   │
│ Input: Query + 20 documents                 │
│ Process: Cross-encoder 交叉编码相关性打分    │
│ Output: Top 6 (RERANK_TOP_N)                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Step 4: LLM 生成答案                         │
│ ─────────────────────────────────────────── │
│ API: http://10.168.2.110:8000/v1/chat/...   │
│ Model: Qwen3-30B-A3B                        │
│ Context: Top 6 菜谱文档                      │
│ Output: 自然语言答案                         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
    返回用户: "红烧肉的做法：..."
```

---

## 🔧 常见操作

### 添加菜谱到知识库

```bash
# 单个菜谱
curl -X POST "http://localhost:8000/api/v1/knowledge/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "鱼香肉丝",
    "category": "川菜",
    "difficulty": "中等",
    "ingredients": ["猪里脊300g", "木耳50g", "胡萝卜1根"],
    "steps": ["切丝", "腌制", "调汁", "快炒"],
    "tips": "火候要大，快速翻炒"
  }'
```

### 批量导入菜谱

```bash
# 使用爬虫导入（推荐）
python -m gustobot.crawler.cli wikipedia --query "川菜" --import-kb --limit 10

# 从 JSON 文件导入
python scripts/import_recipes.py --file data/recipe.json --batch-size 100
```

### 清空知识库

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/clear"
```

### 查看知识库状态

```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/stats" | jq
```

**预期响应**:
```json
{
  "total_entities": 15234,
  "chunk_size": 512,
  "chunk_overlap": 80,
  "embedding_model": "bge-m3",
  "reranker_enabled": true
}
```

---

## 🐛 调试和监控

### 查看实时日志

```bash
# 查看服务器日志
docker-compose logs -f server

# 查看 Neo4j 日志
docker-compose logs -f neo4j

# 查看 Milvus 日志
docker-compose logs -f milvus-standalone
```

### 关键日志位置

在日志中查找以下信息：

**Embedding 调用**:
```
[INFO] Embedding query using bge-m3
[DEBUG] OpenAI API base: http://10.168.2.250:9997/v1
```

**Milvus 检索**:
```
[INFO] Milvus search: recall_k=20
[DEBUG] Found 20 candidates with similarity > 0.7
```

**Reranker 调用**:
```
[INFO] Reranker enabled: custom @ http://10.168.2.250:9997/v1
[DEBUG] Sending 20 documents for reranking
[INFO] Reranked 20 docs → Top 6
```

### 测试外部服务连通性

```bash
# 测试 Embedding 服务
curl -X POST "http://10.168.2.250:9997/v1/embeddings" \
  -H "Authorization: Bearer sk-72tkvudyGLPMi" \
  -H "Content-Type: application/json" \
  -d '{"model": "bge-m3", "input": "测试文本"}' | jq

# 测试 Reranker 服务
curl -X POST "http://10.168.2.250:9997/v1/rerank" \
  -H "Authorization: Bearer sk-72tkvudyGLPMi" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bge-reranker-large",
    "query": "红烧肉",
    "documents": ["红烧肉做法", "糖醋排骨做法"],
    "top_n": 2
  }' | jq

# 测试 LLM 服务
curl -X POST "http://10.168.2.110:8000/v1/chat/completions" \
  -H "Authorization: Bearer vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-30B-A3B",
    "messages": [{"role": "user", "content": "你好"}]
  }' | jq
```

---

## ⚙️ 性能调优

### 检索参数调整

编辑 `.env` 文件：

```bash
# 高准确率配置（牺牲速度）
RERANK_MAX_CANDIDATES=50  # 召回更多候选
RERANK_TOP_N=5            # 返回 Top 5
KB_SIMILARITY_THRESHOLD=0.8  # 提高相似度阈值

# 低延迟配置（牺牲准确率）
RERANK_MAX_CANDIDATES=10  # 召回更少候选
RERANK_TOP_N=3            # 返回 Top 3
KB_SIMILARITY_THRESHOLD=0.6  # 降低相似度阈值

# 平衡配置（当前默认）⭐
RERANK_MAX_CANDIDATES=20
RERANK_TOP_N=6
KB_SIMILARITY_THRESHOLD=0.7
```

修改后重启服务：
```bash
docker-compose restart server
```

### 缓存配置优化

```bash
# Redis 语义缓存设置
REDIS_CACHE_EXPIRE=43200      # 缓存过期时间（12小时）
REDIS_CACHE_THRESHOLD=0.92    # 语义相似度阈值
REDIS_CACHE_MAX_SIZE=1000     # 最大缓存条目数

# 对话历史保留
CONVERSATION_HISTORY_TTL=259200        # 3天
CONVERSATION_HISTORY_MAX_MESSAGES=200  # 每个会话最多200条消息
```

---

## 🎯 API 端点速查

### 知识库管理
- `POST /api/v1/knowledge/recipes` - 添加单个菜谱
- `POST /api/v1/knowledge/recipes/batch` - 批量添加菜谱
- `POST /api/v1/knowledge/search` - 检索知识库
- `DELETE /api/v1/knowledge/recipes/{recipe_id}` - 删除菜谱
- `POST /api/v1/knowledge/clear` - 清空知识库
- `GET /api/v1/knowledge/stats` - 获取统计信息

### 对话接口
- `POST /api/v1/chat/` - 发送对话消息
- `GET /api/v1/chat/history/{session_id}` - 获取对话历史
- `DELETE /api/v1/chat/history/{session_id}` - 清除对话历史

### Neo4j 知识图谱
- `POST /api/v1/neo4j/query` - 执行 Cypher 查询
- `GET /api/v1/neo4j/graph` - 获取图谱可视化数据
- `POST /api/v1/neo4j/qa` - 知识图谱问答

### GraphRAG
- `POST /api/v1/graphrag/query` - GraphRAG 查询
- `POST /api/v1/graphrag/index` - 构建 GraphRAG 索引

完整 API 文档: http://localhost:8000/docs

---

## 📦 依赖服务检查

```bash
# 检查 Docker 服务状态
docker-compose ps

# 预期输出：
# NAME                STATUS
# gustobot-server     Up 5 minutes
# gustobot-neo4j      Up 5 minutes
# gustobot-mysql      Up 5 minutes
# gustobot-redis      Up 5 minutes
# gustobot-milvus     Up 5 minutes
# gustobot-etcd       Up 5 minutes
# gustobot-minio      Up 5 minutes

# 检查端口占用
netstat -tuln | grep -E '8000|17474|13306|6379|19530'

# 测试数据库连接
docker-compose exec neo4j cypher-shell -u neo4j -p recipepass "MATCH (n) RETURN count(n) as total"
docker-compose exec redis redis-cli ping
```

---

## 🚨 常见问题

### 问题 1: Embedding 服务连接失败

**症状**: 日志显示 `Connection refused` 或 `Timeout`

**解决方案**:
```bash
# 1. 检查服务是否可达
curl -I http://10.168.2.250:9997/v1/embeddings

# 2. 检查 API Key 是否正确
grep EMBEDDING_API_KEY .env

# 3. 查看详细错误日志
docker-compose logs -f server | grep -i embedding
```

### 问题 2: Reranker 返回空结果

**症状**: 日志显示 `Reranker returned no results`

**解决方案**:
```bash
# 1. 测试 Reranker 端点
curl -X POST "http://10.168.2.250:9997/v1/rerank" \
  -H "Authorization: Bearer sk-72tkvudyGLPMi" \
  -H "Content-Type: application/json" \
  -d '{"model": "bge-reranker-large", "query": "test", "documents": ["doc1"], "top_n": 1}'

# 2. 检查配置
python3 -c "from gustobot.config.settings import settings; print(settings.RERANK_BASE_URL, settings.RERANK_ENDPOINT)"

# 3. 临时禁用 Reranker 测试
# 编辑 .env: RERANK_ENABLED=false
# docker-compose restart server
```

### 问题 3: Milvus 连接失败

**症状**: `Connection to Milvus failed`

**解决方案**:
```bash
# 1. 检查 Milvus 容器状态
docker-compose ps milvus-standalone

# 2. 重启 Milvus
docker-compose restart milvus-standalone etcd minio

# 3. 查看 Milvus 日志
docker-compose logs -f milvus-standalone

# 4. 验证端口
telnet localhost 19530
```

---

## 📚 更多文档

- **集成总结**: [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
- **集成验证**: [INTEGRATION_VERIFICATION.md](INTEGRATION_VERIFICATION.md)
- **项目架构**: [CLAUDE.md](../CLAUDE.md)
- **爬虫指南**: [docs/crawler_guide.md](crawler_guide.md)
- **知识图谱**: [docs/recipe_kg_schema.md](recipe_kg_schema.md)
- **API 文档**: http://localhost:8000/docs

---

**祝使用愉快！** 🎉

如有问题，请查看日志文件或参考上述文档。

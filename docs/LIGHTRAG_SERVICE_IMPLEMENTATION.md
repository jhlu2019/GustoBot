# LightRAG 问答服务实现总结

## 🎯 实现目标

基于 Docker build 时预生成的 LightRAG 索引文件（JSON + GraphML），实现高效的问答检索服务。

---

## 📂 创建的文件

### 1. 核心服务层

**`app/services/lightrag_service.py`** - LightRAG 问答检索服务

**功能**:
- 加载预生成的索引文件（Docker build 时生成）
- 支持多种检索模式：naive、local、global、hybrid
- 支持流式和非流式响应
- 支持增量文档插入
- 提供索引统计信息

**关键类**:
```python
class LightRAGService:
    async def initialize()              # 初始化并加载索引文件
    async def query()                   # 执行查询（支持流式）
    async def query_structured()        # 结构化查询响应
    async def insert_documents()        # 增量插入文档
    async def cleanup()                 # 清理资源
    def get_index_stats()               # 获取索引统计

def get_lightrag_service()             # 单例获取服务实例
```

---

### 2. API 路由层

**`app/api/lightrag_router.py`** - FastAPI 路由

**端点**:
- `POST /api/v1/lightrag/query` - 非流式查询
- `POST /api/v1/lightrag/query-stream` - 流式查询（SSE）
- `POST /api/v1/lightrag/insert` - 增量插入文档
- `GET /api/v1/lightrag/stats` - 获取索引统计
- `POST /api/v1/lightrag/test-modes` - 测试所有检索模式

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/lightrag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "红烧肉怎么做？",
    "mode": "hybrid",
    "top_k": 10,
    "stream": false
  }'
```

---

### 3. 测试脚本

**`scripts/test_lightrag_service.py`** - 测试脚本

**功能**:
- 测试所有检索模式（naive、local、global、hybrid）
- 测试流式查询
- 测试结构化查询
- 显示索引文件统计

**运行**:
```bash
docker-compose exec server python scripts/test_lightrag_service.py
```

---

### 4. 文档

**`docs/lightrag_service_guide.md`** - 完整使用指南

**内容**:
- 架构设计图
- 快速开始指南
- API 端点详细说明
- 检索模式对比
- Python/JavaScript/cURL 示例代码
- 配置说明
- 故障排查
- 性能优化建议
- 最佳实践

---

## 🏗️ 架构设计

### 数据流

```
┌─────────────────────────────────────────────┐
│         Docker Build 时                      │
│                                             │
│  data/recipe.json                           │
│         ↓                                   │
│  scripts/init_lightrag.py                   │
│         ↓                                   │
│  LightRAG.ainsert(recipes)                  │
│         ↓                                   │
│  生成索引文件（打包进镜像）:                  │
│  ├─ graph_chunk_entity_relation.graphml     │
│  ├─ kv_store_doc_status.json                │
│  ├─ kv_store_full_docs.json                 │
│  ├─ kv_store_text_chunks.json               │
│  ├─ vdb_chunks.json                         │
│  ├─ vdb_entities.json                       │
│  └─ vdb_relationships.json                  │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│         运行时（容器启动）                    │
│                                             │
│  LightRAGService.initialize()               │
│         ↓                                   │
│  加载预生成的索引文件                         │
│         ↓                                   │
│  FastAPI 路由 /api/v1/lightrag/*            │
│         ↓                                   │
│  用户查询 → 检索 → 返回答案                  │
└─────────────────────────────────────────────┘
```

### 服务层次

```
┌──────────────────────────────────────┐
│   API Layer (FastAPI Routes)        │
│   app/api/lightrag_router.py         │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│   Service Layer                      │
│   app/services/lightrag_service.py   │
│   - LightRAGService                  │
│   - get_lightrag_service()           │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│   LightRAG Library                   │
│   - LightRAG.aquery()                │
│   - LightRAG.ainsert()               │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│   Index Files (Pregenerated)         │
│   /app/data/lightrag/*.json          │
│   /app/data/lightrag/*.graphml       │
└──────────────────────────────────────┘
```

---

## 🔧 修改的文件

### 1. `app/main.py`

**修改**:
- 导入 `lightrag_router`
- 注册路由: `app.include_router(lightrag_router.router, prefix=settings.API_V1_PREFIX)`
- 添加 shutdown 时清理 LightRAG 资源

**新增代码**:
```python
from .api import lightrag_router
from .services.lightrag_service import get_lightrag_service

# 注册路由
app.include_router(lightrag_router.router, prefix=settings.API_V1_PREFIX)

# Shutdown 时清理
@app.on_event("shutdown")
async def shutdown_event():
    # ... (Neo4j cleanup)

    # Cleanup LightRAG resources
    try:
        lightrag_service = get_lightrag_service()
        await lightrag_service.cleanup()
    except Exception as exc:
        logger.warning(f"Failed to cleanup LightRAG service: {exc}")
```

---

### 2. `app/api/__init__.py`

**修改**:
- 添加 `lightrag_router` 到导入和导出

**修改后**:
```python
from . import chat_router, knowledge_router, lightrag_router

__all__ = ["chat_router", "knowledge_router", "lightrag_router"]
```

---

## 📊 索引文件说明

### 预生成的索引文件

Docker build 时生成以下文件（位于 `/app/data/lightrag/`）:

| 文件名 | 大小 | 说明 |
|--------|------|------|
| `graph_chunk_entity_relation.graphml` | ~15MB | 图谱结构（实体和关系） |
| `kv_store_doc_status.json` | ~100KB | 文档状态追踪 |
| `kv_store_full_docs.json` | ~25MB | 完整文档内容 |
| `kv_store_text_chunks.json` | ~5MB | 文本块索引 |
| `vdb_chunks.json` | ~2MB | 文本块向量 |
| `vdb_entities.json` | ~1.5MB | 实体向量 |
| `vdb_relationships.json` | ~1MB | 关系向量 |

**总大小**: ~48.6MB

---

## 🚀 使用示例

### 1. Python 代码

```python
from app.services.lightrag_service import get_lightrag_service

async def query_example():
    service = get_lightrag_service()
    await service.initialize()

    # 查询
    response = await service.query(
        query="红烧肉怎么做？",
        mode="hybrid",
        top_k=10,
        stream=False
    )
    print(response)

    await service.cleanup()
```

### 2. cURL 命令

```bash
# 非流式查询
curl -X POST "http://localhost:8000/api/v1/lightrag/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "红烧肉怎么做？", "mode": "hybrid", "top_k": 10, "stream": false}'

# 流式查询
curl -X POST "http://localhost:8000/api/v1/lightrag/query-stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "宫保鸡丁怎么做？", "mode": "hybrid"}'

# 获取统计
curl "http://localhost:8000/api/v1/lightrag/stats"
```

### 3. JavaScript 代码

```javascript
// 非流式查询
const response = await fetch('http://localhost:8000/api/v1/lightrag/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '红烧肉怎么做？',
    mode: 'hybrid',
    top_k: 10,
    stream: false
  })
});

const result = await response.json();
console.log(result.response);
```

---

## 🎯 检索模式

### 模式对比

| 模式 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| **naive** | 直接向量搜索 | 速度快 | 可能遗漏关联信息 | 简单关键词查询 |
| **local** | 局部图谱检索 | 关注特定实体 | 范围有限 | 聚焦查询 |
| **global** | 全局图谱检索 | 综合性强 | 速度较慢 | 需要多知识点 |
| **hybrid** | 混合检索 | 平衡速度和准确度 | - | **推荐默认** |

### 推荐

**默认使用 `hybrid` 模式**，它结合了向量搜索和图谱检索的优势。

---

## 🔍 测试验证

### 1. 运行测试脚本

```bash
docker-compose exec server python scripts/test_lightrag_service.py
```

**输出示例**:
```
============================================================
索引文件统计
============================================================

工作目录: /app/data/lightrag
总大小: 48.5 MB
已初始化: False

文件详情:
  ✓ graph_chunk_entity_relation.graphml: 15.0 MB
  ✓ kv_store_doc_status.json: 0.1 MB
  ✓ kv_store_full_docs.json: 25.0 MB
  ✓ kv_store_text_chunks.json: 5.0 MB
  ✓ vdb_chunks.json: 2.0 MB
  ✓ vdb_entities.json: 1.5 MB
  ✓ vdb_relationships.json: 1.0 MB

============================================================
Query mode: hybrid
============================================================

回答:
红烧肉的做法如下...（详细步骤）
```

### 2. API 测试

访问 FastAPI 文档: `http://localhost:8000/docs`

在 Swagger UI 中测试各个端点。

---

## ⚙️ 配置

### 环境变量（`.env`）

```bash
# LightRAG 配置
LIGHTRAG_WORKING_DIR=./data/lightrag
LIGHTRAG_RETRIEVAL_MODE=hybrid
LIGHTRAG_TOP_K=10
LIGHTRAG_MAX_TOKEN_SIZE=4096

# OpenAI 配置（必需）
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Docker Build 配置
INIT_LIGHTRAG_ON_BUILD=true   # 构建时初始化
LIGHTRAG_INIT_LIMIT=          # 留空=全部，10=测试
```

---

## 🐛 故障排查

### 问题 1: 索引文件不存在

**症状**: 查询返回空结果

**检查**:
```bash
docker-compose exec server ls -lh /app/data/lightrag/
```

**解决**:
```bash
# 重新构建镜像
docker-compose down
docker-compose build --no-cache server
docker-compose up -d
```

### 问题 2: API 返回 500 错误

**检查日志**:
```bash
docker-compose logs -f server
```

**常见原因**:
- OpenAI API key 未配置
- 索引文件损坏
- 内存不足

---

## 📈 性能优化

1. **索引预生成**: Docker build 时生成，运行时直接加载（无需重建）
2. **单例模式**: `get_lightrag_service()` 确保全局只有一个实例
3. **流式响应**: 提升用户体验，实时返回结果
4. **批量插入**: 增量插入文档时使用批处理

---

## ✅ 总结

### 实现的功能

✅ 基于预生成索引文件的问答检索
✅ 多种检索模式（naive/local/global/hybrid）
✅ 流式和非流式响应
✅ 增量文档插入
✅ 索引统计信息
✅ 完整的 REST API
✅ 测试脚本和文档

### 与现有系统的集成

- **Neo4j 知识图谱**: 结构化实体关系查询（独立系统）
- **LightRAG**: 非结构化文本语义搜索（本服务）
- **两者互补**: Neo4j 用于精确关系查询，LightRAG 用于自然语言问答

### 下一步

1. 在前端集成 LightRAG 查询
2. 添加更多测试用例
3. 监控查询性能和缓存命中率
4. 定期更新索引（增量插入新菜谱）

---

## 📚 参考资料

- **服务实现**: `app/services/lightrag_service.py`
- **API 路由**: `app/api/lightrag_router.py`
- **测试脚本**: `scripts/test_lightrag_service.py`
- **使用指南**: `docs/lightrag_service_guide.md`
- **LightRAG 官方**: https://github.com/HKUDS/LightRAG

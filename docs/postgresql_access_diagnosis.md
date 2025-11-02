# PostgreSQL 访问问题诊断报告

## 问题描述
kb-query 路由无法访问 PostgreSQL 中的历史菜谱数据

## 诊断结果

### 1. PostgreSQL 数据状态 ✅
- **数据库**: `vector_db` (kb_postgres容器)
- **表**:
  - `historical_recipes` - 8条记录
  - `historical_recipes_vector` - 空表（等待embedding）
  - `searchable_documents` - 其他数据
- **连接**: 正常运行在端口5433

### 2. kb_ingest 服务状态 ⚠️
- **服务**: 运行正常 (http://localhost:8100)
- **API路径**: `/api/search` (不是 `/api/v1/knowledge/search`)
- **问题**:
  - 缺少 embedding API 配置 (500错误)
  - 环境变量未设置:
    - `KB_EMBEDDING_API_KEY`
    - `KB_EMBEDDING_BASE_URL`
    - `KB_EMBEDDING_MODEL`

### 3. Backend 访问问题 ❌
- **期望URL**: `http://kb_ingest:8000/api/v1/knowledge/search`
- **实际URL**: `http://kb_ingest:8000/api/search`
- **结果**: 404 Not Found
- **原因**: API 路径不匹配

### 4. 数据流程
```
用户查询 → kb-query路由 → 尝试PostgreSQL
                      ↓
                 访问kb_ingest服务
                      ↓
                 404错误 (路径错误)
                      ↓
                 Fallback到Milvus ✅
                      ↓
                 返回结果
```

## 问题根本原因

1. **API路径不匹配**
   - Backend代码中的路径: `/api/v1/knowledge/search`
   - kb_ingest实际路径: `/api/search`

2. **kb_ingest配置不完整**
   - 缺少embedding服务配置
   - 无法生成向量进行相似度搜索

3. **数据格式问题**
   - PostgreSQL数据需要embedding列
   - 当前只有文本数据，缺少向量

## 解决方案

### 方案1: 修复API路径 (推荐)
修改 `gustobot/application/agents/kg_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`:
```python
# 第264-266行
postgres_search_url = (
    f"{ingest_service_base}/api/search" if ingest_service_base else None  # 修改这里
)
```

### 方案2: 配置kb_ingest环境变量
在 `.env` 或 docker-compose.yml 中添加:
```env
KB_EMBEDDING_API_KEY=your_openai_api_key
KB_EMBEDDING_BASE_URL=https://api.openai.com/v1
KB_EMBEDDING_MODEL=text-embedding-3-small
```

### 方案3: 直接PostgreSQL查询
绕过kb_ingest，直接在backend中查询PostgreSQL:
```python
# 使用全文搜索而不是向量搜索
cur.execute("""
    SELECT * FROM historical_recipes
    WHERE to_tsvector('chinese', dish_name || ' ' || historical_source || ' ' || historical_description)
    @@ plainto_tsquery('chinese', %s)
""", (query,))
```

## 当前状态总结

- ✅ PostgreSQL中有数据 (8条历史记录)
- ✅ Milvus中有数据并正常工作
- ❌ 无法通过kb_ingest访问PostgreSQL
- ⚠️ 系统依赖Milvus作为fallback

## 建议

短期方案：
1. 修复API路径不匹配问题
2. 配置kb_ingest的embedding服务

长期方案：
1. 实现PostgreSQL全文搜索（不依赖embedding）
2. 建立混合搜索机制（PostgreSQL + Milvus）
3. 为历史数据生成准确的向量表示

## 影响评估

- **用户体验**: 查询仍然通过Milvus返回结果，但可能不够精确
- **数据完整性**: PostgreSQL中的结构化数据未被充分利用
- **系统性能**: 增加了不必要的fallback延迟
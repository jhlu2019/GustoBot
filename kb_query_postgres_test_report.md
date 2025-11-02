# kb-query PostgreSQL 数据测试报告

## 测试时间
2025-11-02

## 测试目标
验证 kb-query 路由能否正确查询 PostgreSQL 中的历史菜谱数据

## 测试过程

### 1. 数据准备 ✅
- **数据源**: `F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx`
- **数据内容**: 8条历史菜谱数据，包括菜品名称、历史源头、朝代、地区等
- **导入状态**: 成功导入到 PostgreSQL `historical_recipes` 表

### 2. 路由测试 ✅
测试问题：
- "东坡肉的历史"
- "麻婆豆腐的来历"
- "佛跳墙的历史典故"

**路由结果**: 所有问题都成功路由到 `kb-query`

### 3. 数据查询测试 ⚠️

#### 问题发现
1. **API端点不匹配**
   - Backend 期望: `http://kb_ingest:8000/api/v1/knowledge/search`
   - 实际端点: `http://kb_ingest:8000/api/search`

2. **服务配置缺失**
   - kb_ingest 服务需要 embedding API 密钥
   - 缺少的环境变量:
     - `KB_EMBEDDING_API_KEY`
     - `KB_EMBEDDING_BASE_URL`
     - `KB_EMBEDDING_MODEL`

3. **查询流程**
   ```
   kb-query → 尝试 PostgreSQL (404错误) → Fallback到 Milvus → 返回空结果
   ```

## 当前状态

### PostgreSQL 数据 ✅
```sql
SELECT dish_name, dynasty FROM historical_recipes;
 红烧肉    | 宋代
 宫保鸡丁  | 清代
 麻婆豆腐  | 清代
 鱼香肉丝  | 民国
 东坡肉    | 宋代
 佛跳墙    | 清代
 糖醋排骨  | 唐代
 北京烤鸭  | 明代
```

### kb-query 工作流程 ✅
- 路由识别正常
- 决策使用 PostgreSQL + Milvus 双重查询
- PostgreSQL 查询失败后自动 fallback 到 Milvus

### 主要问题 ❌
1. kb_ingest 服务配置不完整
2. API 路径不匹配
3. PostgreSQL 数据未被有效利用

## 解决方案

### 方案1：配置 kb_ingest 服务
在 `.env` 文件中添加：
```env
KB_EMBEDDING_API_KEY=your_openai_api_key
KB_EMBEDDING_BASE_URL=https://api.openai.com/v1
KB_EMBEDDING_MODEL=text-embedding-3-small
```

### 方案2：修改 Backend 代码
更新 PostgreSQL 查询端点路径：
```python
# 从
postgres_search_url = f"{ingest_service_base}/api/v1/knowledge/search"
# 改为
postgres_search_url = f"{ingest_service_base}/api/search"
```

### 方案3：直接 SQL 查询
绕过 kb_ingest，直接在后端查询 PostgreSQL：
```python
async def query_postgresql_direct(query: str):
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM historical_recipes
            WHERE to_tsvector('chinese', dish_name || ' ' ||
                   COALESCE(historical_source, '') || ' ' ||
                   COALESCE(historical_description, ''))
            @@ plainto_tsquery('chinese', %s)
        """, (query,))
        return cur.fetchall()
```

## 测试结论

### 成功部分
- ✅ 数据成功导入 PostgreSQL
- ✅ kb-query 路由识别正确
- ✅ 系统具备 fallback 机制

### 待改进
- ❌ PostgreSQL 数据未被有效查询
- ❌ kb_ingest 服务配置不完整
- ❌ 返回"暂未找到相关记载"

### 总体评价
kb-query 路由系统架构合理，能够正确识别历史相关查询并决定使用 PostgreSQL。但由于服务配置问题，实际查询未能成功。建议优先配置 kb_ingest 服务的环境变量以启用完整的查询功能。

## 后续建议

1. **短期**: 配置 kb_ingest 所需的环境变量
2. **中期**: 为历史数据生成 embedding，提升查询效果
3. **长期**: 实现混合搜索（全文搜索 + 向量搜索）
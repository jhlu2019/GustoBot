# 快速开始指南

本文档提供企业知识库向量检索服务的详细配置和使用说明。

## 目录

- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [数据接入](#数据接入)
- [数据检索](#数据检索)
- [运维管理](#运维管理)

## 系统要求

### 硬件要求

- CPU: 2核及以上
- 内存: 4GB 及以上
- 磁盘: 20GB 可用空间

### 软件要求

- Docker 20.10 或更高版本
- Docker Compose 1.29 或更高版本
- 网络访问：能够访问 LLM 和 Embedding 服务

## 安装部署

### 1. 获取代码

```bash
cd knowledge-ingestion-service
```

### 2. 配置环境变量

复制示例配置文件并编辑：

```bash
cp .env.example .env
vi .env
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

预期输出：
```
      Name                    Command               State           Ports
---------------------------------------------------------------------------------
temp30_api_1        uvicorn app.main:app ...   Up      0.0.0.0:8000->8000/tcp
temp30_postgres_1   docker-entrypoint.sh ...   Up      0.0.0.0:5432->5432/tcp
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 预期返回
{"status":"ok"}

# 访问 API 文档
open http://localhost:8000/docs
```

## 配置说明

### 核心配置项

#### LLM 服务配置

```bash
# LLM 提供商（固定为 openai，兼容 OpenAI API 的服务）
LLM_PROVIDER=openai

# LLM 模型名称
LLM_MODEL=Qwen3-30B-A3B

# LLM API Key
LLM_API_KEY=sk-xxxxxxxxxxxxxx

# LLM 服务地址
LLM_BASE_URL=http://10.168.2.110:8000/v1
```

#### Embedding 服务配置

```bash
# Embedding 提供商
EMBEDDING_PROVIDER=openai

# Embedding 模型
EMBEDDING_MODEL=bge-m3

# Embedding API Key
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxx

# Embedding 服务地址
EMBEDDING_BASE_URL=http://10.168.2.110:9997/v1

# 向量维度（必须与模型匹配）
EMBEDDING_DIMENSION=1024
```

#### Reranker 服务配置（可选，但强烈推荐）

```bash
# 是否启用 Rerank
RERANK_ENABLED=true

# Rerank 提供商（固定为 custom）
RERANK_PROVIDER=custom

# Reranker 服务基础地址
RERANK_BASE_URL=http://10.168.2.250:9997/v1

# Rerank 接口路径（重要：必须配置，不能为空）
RERANK_ENDPOINT=/rerank

# Rerank 模型
RERANK_MODEL=bge-reranker-large

# Rerank API Key
RERANK_API_KEY=sk-72tkvudyGLPMi

# Rerank 候选数量
RERANK_MAX_CANDIDATES=20

# Rerank 返回结果数
RERANK_TOP_N=6

# Rerank 超时时间（秒）
RERANK_TIMEOUT=30
```

**重要提示**：
- `RERANK_ENDPOINT` 不能为空，否则会出现404错误
- 完整的请求URL = `{RERANK_BASE_URL}{RERANK_ENDPOINT}`
- 例如：`http://10.168.2.250:9997/v1/rerank`

#### 数据库配置

```bash
# 数据库主机（容器内使用服务名）
PGHOST=postgres

# 数据库端口
PGPORT=5432

# 数据库名称
PGDATABASE=vector_db

# 数据库用户
PGUSER=postgres

# 数据库密码
PGPASSWORD=postgres
```

#### 处理模式配置

```bash
# 是否启用 LLM 重写
USE_LLM=true

# LLM 失败时是否回退到扁平化模式
LLM_FALLBACK_TO_FLATTEN=false

# 批处理大小
BATCH_SIZE=32

# 自定义 Prompt 配置文件路径（可选）
PROMPT_CONFIG_PATH=prompts/custom.json
```

### 配置最佳实践

#### 生产环境

```bash
USE_LLM=true
LLM_FALLBACK_TO_FLATTEN=true  # 启用回退机制
RERANK_ENABLED=true           # 启用精排
BATCH_SIZE=32                 # 批量处理
```

#### 测试环境

```bash
USE_LLM=false                 # 使用快速模式
RERANK_ENABLED=false          # 禁用精排
BATCH_SIZE=16                 # 小批量处理
```

#### 内网环境

如果服务部署在内网，需要配置代理例外：

```bash
export NO_PROXY="localhost,127.0.0.1,10.168.2.110,postgres"
export no_proxy="localhost,127.0.0.1,10.168.2.110,postgres"
```

## 数据接入

### Excel 文件接入

#### 准备数据文件

1. 将 Excel 文件放入 `data/` 目录
2. 确保文件格式正确（.xlsx）
3. 支持多个 sheet

#### 发起导入请求

**全量导入**（首次使用）

```bash
curl -X POST http://localhost:8000/api/ingest/excel \
  -H "Content-Type: application/json" \
  -d '{
    "excel_path": "/app/data/企业数据.xlsx",
    "incremental": false
  }'
```

**增量导入**（日常更新，推荐）

```bash
curl -X POST http://localhost:8000/api/ingest/excel \
  -H "Content-Type: application/json" \
  -d '{
    "excel_path": "/app/data/企业数据.xlsx",
    "incremental": true
  }'
```

**增量模式工作原理**：
1. 系统计算每条数据的MD5哈希值（基于原始数据）
2. 查询数据库中已存在记录的哈希值
3. 比对决策：
   - 哈希值相同 → 数据未变化，跳过处理（节省成本）
   - 哈希值不同 → 数据已修改，重新处理
   - 记录不存在 → 新数据，需要处理

**优势**：
- 自动检测内容变化，无需手动标记
- 大幅降低LLM和Embedding调用成本（通常可节省95%+）
- 支持文件任意修改，自动增量更新

#### 查看处理进度

```bash
# 实时查看日志
docker-compose logs -f api

# 查看最近日志
docker-compose logs --tail=100 api
```

关键日志示例：
```
2025-01-24 10:30:15 - INFO - [1/17] 处理工作表: 企业信息
2025-01-24 10:30:16 - INFO - 共 150 行数据
2025-01-24 10:30:45 - INFO - ✓ 嵌入并入库完成，共处理 150 条
2025-01-24 10:30:45 - INFO - ✅ 所有处理完成！
```

增量模式日志：
```
2025-01-24 10:35:20 - INFO - 从数据库查询到 150 条现有记录的哈希
2025-01-24 10:35:21 - INFO - 增量检测结果: 需更新 5 条, 跳过 145 条
2025-01-24 10:35:35 - INFO - ✓ 嵌入并入库完成，共处理 5 条
```

### MySQL 表接入

#### 基础导入

```bash
curl -X POST http://localhost:8000/api/ingest/mysql \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "mysql+pymysql://username:password@host:3306/database",
    "table": "users",
    "mode": "rewrite",
    "id_column": "user_id"
  }'
```

#### 条件过滤导入

```bash
curl -X POST http://localhost:8000/api/ingest/mysql \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "mysql+pymysql://user:pass@host/db",
    "table": "orders",
    "where": "order_date >= '\''2024-01-01'\'' AND status = '\''completed'\''",
    "limit": 10000,
    "id_column": "order_id"
  }'
```

#### 分批处理大表

```bash
# 第一批
curl -X POST http://localhost:8000/api/ingest/mysql \
  -d '{
    "table": "large_table",
    "where": "id >= 1 AND id < 10000",
    "id_column": "id"
  }'

# 第二批
curl -X POST http://localhost:8000/api/ingest/mysql \
  -d '{
    "table": "large_table",
    "where": "id >= 10000 AND id < 20000",
    "id_column": "id"
  }'
```

### 验证导入结果

#### 查看数据统计

```bash
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  source_table,
  COUNT(*) as record_count,
  COUNT(DISTINCT company_name) as company_count,
  MIN(created_at) as first_import,
  MAX(created_at) as last_import
FROM searchable_documents
GROUP BY source_table
ORDER BY record_count DESC;
"
```

#### 抽样查看数据

```bash
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  id,
  source_table,
  LEFT(content, 100) as content_preview,
  metadata->>'企业名称' as company,
  created_at
FROM searchable_documents
ORDER BY created_at DESC
LIMIT 5;
"
```

## 数据检索

### 基础向量检索

#### 简单查询

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能相关政策",
    "top_k": 5
  }'
```

#### 指定数据源查询

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "智能制造技术",
    "top_k": 10,
    "source_tables": ["企业专利", "企业产品"]
  }'
```

#### 设置相似度阈值

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "新能源汽车",
    "top_k": 10,
    "threshold": 0.7,
    "metric": "cosine"
  }'
```

#### 按企业过滤

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "专利技术",
    "top_k": 5,
    "company_filter": "常州纳欧"
  }'
```

### 混合召回检索

#### 基础混合检索

```bash
curl -X POST http://localhost:8000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "数字化转型扶持政策",
    "vector_top_k": 20,
    "rerank_top_k": 10
  }'
```

#### 指定来源的混合检索

```bash
curl -X POST http://localhost:8000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "企业融资支持政策",
    "vector_top_k": 30,
    "rerank_top_k": 15,
    "source_tables": ["政策数据", "企业融资信息"]
  }'
```

### 解析检索结果

#### 结果结构说明

```json
{
  "query": "查询文本",
  "results": [
    {
      "id": 123,                    // 记录ID
      "source_table": "企业信息",   // 来源表
      "source_id": "42",            // 原始记录ID
      "content": "处理后的文本...", // 可读文本
      "similarity": 0.8234,         // 余弦相似度
      "distance": 0.1766,           // 向量距离
      "metadata": {                 // 原始数据
        "企业名称": "XX科技有限公司",
        "注册资本": "1000万元",
        ...
      }
    }
  ],
  "count": 5
}
```

#### 混合检索结果结构

```json
{
  "query": "查询文本",
  "results": [                  // 混合结果（优先级最高）
    {
      "id": 45,
      "source_table": "政策数据",
      "content": "...",
      "similarity": 0.7823,     // 向量相似度 (0-1)
      "rerank_score": 0.9512,   // Rerank 分数 (0-1，更重要)
      "metadata": {...}
    }
  ],
  "count": 10
}
```

**混合召回策略说明**：

1. **向量检索阶段**：召回 `vector_top_k` 个候选（如20个）
2. **Rerank精排阶段**：对候选进行精排，返回 `rerank_top_k` 个（如10个）
3. **结果合并策略**：
   ```
   IF Rerank成功:
       向量结果IDs = {1, 2, 3, 4, 5, ..., 20}
       Rerank结果IDs = {3, 7, 12, 15, 20, ..., 45}

       IF 有交集 (如 {3, 7, 12, 15, 20}):
           返回交集部分，按Rerank分数排序
       ELSE:
           仅返回Rerank精排结果
   ELSE:
       返回向量检索结果
   ```

**分数说明**：
- `similarity`: 向量余弦相似度（越高越相似）
- `rerank_score`: 语义相关性分数（越高越相关）
- 排序优先级：`rerank_score` > `similarity`

## 运维管理

### 服务管理

#### 启动服务

```bash
docker-compose up -d
```

#### 停止服务

```bash
docker-compose down
```

#### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 只重启 API 服务
docker-compose restart api
```

#### 查看服务状态

```bash
docker-compose ps
```

#### 查看资源使用

```bash
docker stats
```

### 日志管理

#### 查看实时日志

```bash
# API 服务日志
docker-compose logs -f api

# 数据库日志
docker-compose logs -f postgres
```

#### 查看历史日志

```bash
# 最近 100 行
docker-compose logs --tail=100 api

# 特定时间范围
docker-compose logs --since="2025-01-24T10:00:00" api
```

#### 搜索日志

```bash
# 搜索错误日志
docker-compose logs api | grep -i error

# 搜索特定表的处理日志
docker-compose logs api | grep "企业信息"
```

### 数据库管理

#### 连接数据库

```bash
# 使用 psql
docker exec -it temp30_postgres_1 psql -U postgres -d vector_db

# 使用 DBeaver 等图形工具
# Host: localhost
# Port: 5432
# Database: vector_db
# Username: postgres
# Password: postgres
```

#### 数据备份

```bash
# 备份整个数据库
docker exec temp30_postgres_1 pg_dump -U postgres vector_db > backup_$(date +%Y%m%d).sql

# 备份特定表
docker exec temp30_postgres_1 pg_dump -U postgres -t searchable_documents vector_db > documents_backup.sql
```

#### 数据恢复

```bash
# 恢复数据库
docker exec -i temp30_postgres_1 psql -U postgres vector_db < backup_20250124.sql
```

#### 清理数据

```bash
# 删除特定来源的数据
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
DELETE FROM searchable_documents WHERE source_table = '企业信息';
"

# 清空所有数据
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
TRUNCATE TABLE searchable_documents;
"
```

#### 数据库优化

```bash
# 分析表统计信息
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
ANALYZE searchable_documents;
"

# 清理和优化
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
VACUUM ANALYZE searchable_documents;
"

# 查看表大小
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  pg_size_pretty(pg_total_relation_size('searchable_documents')) as total_size,
  pg_size_pretty(pg_relation_size('searchable_documents')) as table_size,
  pg_size_pretty(pg_indexes_size('searchable_documents')) as indexes_size;
"
```

### 性能监控

#### 查询性能统计

```bash
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  idx_tup_fetch
FROM pg_stat_user_tables
WHERE tablename = 'searchable_documents';
"
```

#### 索引使用情况

```bash
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'searchable_documents';
"
```

### 故障排查

#### 服务无法启动

```bash
# 查看详细错误信息
docker-compose logs api

# 检查端口占用
netstat -tlnp | grep 8000
netstat -tlnp | grep 5432

# 检查磁盘空间
df -h
```

#### LLM/Embedding 连接失败

```bash
# 测试网络连通性
curl -v http://10.168.2.110:8000/v1/models
curl -v http://10.168.2.250:9997/v1/models

# 检查代理设置
echo $http_proxy
echo $NO_PROXY

# 清除代理
unset http_proxy https_proxy
export NO_PROXY="localhost,127.0.0.1,10.168.2.110,10.168.2.250,postgres"
```

#### Rerank 服务返回 500/404 错误

**问题诊断**：

```bash
# 1. 检查配置
docker-compose exec api env | grep RERANK

# 2. 测试 Rerank 服务
curl -X POST http://10.168.2.250:9997/v1/rerank \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-72tkvudyGLPMi" \
  -d '{
    "model": "bge-reranker-large",
    "query": "测试查询",
    "documents": ["文档1", "文档2"],
    "top_n": 2
  }'

# 3. 查看API日志
docker-compose logs api | grep -i rerank
```

**常见问题及解决**：

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 404 Not Found | `RERANK_ENDPOINT` 为空或错误 | 设置 `RERANK_ENDPOINT=/rerank` |
| 500 Internal Server Error | 请求格式错误（dict vs string array） | 更新到最新代码 |
| Connection timeout | 网络不通或服务未启动 | 检查服务状态和网络 |
| 401 Unauthorized | API Key错误 | 检查 `RERANK_API_KEY` |

**正确配置示例**：
```bash
RERANK_ENABLED=true
RERANK_PROVIDER=custom
RERANK_BASE_URL=http://10.168.2.250:9997/v1
RERANK_ENDPOINT=/rerank  # 必须配置
RERANK_MODEL=bge-reranker-large
RERANK_API_KEY=sk-72tkvudyGLPMi
```

#### 数据库连接失败

```bash
# 检查数据库服务
docker-compose ps postgres

# 测试连接
docker exec temp30_postgres_1 psql -U postgres -c "SELECT version();"

# 查看数据库日志
docker-compose logs postgres
```

#### 处理速度慢

可能原因及解决方案：

1. **LLM 响应慢**
   - 检查 LLM 服务负载
   - 考虑使用扁平化模式（`USE_LLM=false`）

2. **Embedding 生成慢**
   - 调整批处理大小（`BATCH_SIZE=64`）
   - 检查 Embedding 服务性能

3. **数据库写入慢**
   - 优化索引
   - 增加数据库资源配置

### 更新升级

#### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose down
docker-compose up -d
```

#### 更新依赖

```bash
# 重新构建镜像（包含依赖更新）
docker-compose build --no-cache api

# 重启服务
docker-compose restart api
```

## 最佳实践

### 数据接入最佳实践

1. **首次导入使用全量模式**
   ```bash
   {"incremental": false}
   ```

2. **日常更新使用增量模式**
   ```bash
   {"incremental": true}
   ```

3. **大表分批处理**
   ```bash
   {"limit": 10000, "where": "id > 0 AND id <= 10000"}
   ```

4. **定期备份数据**
   ```bash
   # 每天备份
   0 2 * * * docker exec temp30_postgres_1 pg_dump -U postgres vector_db > /backup/db_$(date +\%Y\%m\%d).sql
   ```

### 检索最佳实践

1. **重要查询使用混合召回**
   - 提升结果质量
   - 使用 Rerank 精排

2. **明确指定数据源**
   - 减少检索范围
   - 提升查询速度

3. **设置合理的阈值**
   - 过滤低质量结果
   - threshold 建议 0.5-0.7

### 运维最佳实践

1. **定期数据库维护**
   ```bash
   # 每周执行
   VACUUM ANALYZE searchable_documents;
   ```

2. **监控服务状态**
   ```bash
   # 定期健康检查
   */5 * * * * curl -sf http://localhost:8000/health || alert
   ```

3. **日志轮转**
   - 配置 Docker 日志驱动
   - 定期清理旧日志

## 附录

### 常用 SQL 查询

```sql
-- 查看所有数据源
SELECT DISTINCT source_table FROM searchable_documents;

-- 查看数据分布
SELECT
  source_table,
  COUNT(*) as count,
  MIN(created_at) as first,
  MAX(created_at) as last
FROM searchable_documents
GROUP BY source_table;

-- 查找重复数据
SELECT source_table, source_id, COUNT(*)
FROM searchable_documents
GROUP BY source_table, source_id
HAVING COUNT(*) > 1;

-- 查看最近导入的数据
SELECT *
FROM searchable_documents
ORDER BY created_at DESC
LIMIT 10;
```

### 环境变量完整列表

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| LLM_PROVIDER | string | openai | LLM 提供商 |
| LLM_MODEL | string | - | LLM 模型名称 |
| LLM_API_KEY | string | - | LLM API Key |
| LLM_BASE_URL | string | - | LLM 服务地址 |
| EMBEDDING_PROVIDER | string | openai | Embedding 提供商 |
| EMBEDDING_MODEL | string | - | Embedding 模型 |
| EMBEDDING_API_KEY | string | - | Embedding API Key |
| EMBEDDING_BASE_URL | string | - | Embedding 服务地址 |
| EMBEDDING_DIMENSION | integer | 1024 | 向量维度 |
| RERANK_ENABLED | boolean | false | 是否启用 Rerank |
| RERANK_PROVIDER | string | custom | Rerank 提供商 |
| RERANK_BASE_URL | string | - | Rerank 服务基础地址 |
| RERANK_ENDPOINT | string | /rerank | Rerank 接口路径（不能为空） |
| RERANK_MODEL | string | - | Rerank 模型 |
| RERANK_API_KEY | string | - | Rerank API Key |
| RERANK_MAX_CANDIDATES | integer | 20 | Rerank 候选数量 |
| RERANK_TOP_N | integer | 6 | Rerank 返回结果数 |
| PGHOST | string | postgres | 数据库主机 |
| PGPORT | integer | 5432 | 数据库端口 |
| PGDATABASE | string | vector_db | 数据库名称 |
| PGUSER | string | postgres | 数据库用户 |
| PGPASSWORD | string | postgres | 数据库密码 |
| USE_LLM | boolean | true | 是否启用 LLM |
| LLM_FALLBACK_TO_FLATTEN | boolean | false | LLM 失败回退 |
| BATCH_SIZE | integer | 32 | 批处理大小 |
| PROMPT_CONFIG_PATH | string | - | 自定义 Prompt 路径 |

 

---
 
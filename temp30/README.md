# 企业知识库向量检索服务

企业级向量知识库系统，支持多数据源接入、智能文本处理和语义检索。适用于企业内部知识管理、智能问答、数据召回等场景。

## 核心能力

- 支持 Excel、MySQL 等多种数据源接入
- 智能文本处理：LLM 重写或字段扁平化
- 向量化存储：基于 pgvector 的高性能向量数据库
- 混合召回：向量检索 + Rerank 精排
- 增量更新：基于内容哈希的智能去重，降低重复处理成本
- RESTful API：标准化接口，易于集成

## 系统架构

```
数据源层              处理层                 存储层              检索层
┌─────────┐        ┌──────────┐          ┌──────────┐       ┌──────────┐
│ Excel   │───────▶│          │          │          │       │          │
│ MySQL   │        │ LLM重写  │─────────▶│ pgvector │◀──────│ 向量检索 │
│ 其他源  │        │ 向量化   │          │ 数据库   │       │ Rerank   │
└─────────┘        └──────────┘          └──────────┘       └──────────┘
```

## 快速开始

### 1. 环境准备

**系统要求**
- Docker 20.10+
- Docker Compose 1.29+
- 至少 4GB 可用内存

**克隆项目**
```bash
git clone <repository-url>
cd knowledge-ingestion-service
```

### 2. 配置服务

编辑 `.env` 文件，配置必要的服务端点：

```bash
# LLM 服务配置（用于文本重写）
LLM_PROVIDER=openai
LLM_MODEL=Qwen3-30B-A3B
LLM_API_KEY=your_api_key
LLM_BASE_URL=http://your-llm-server:8000/v1

# Embedding 服务配置（用于向量生成）
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=bge-m3
EMBEDDING_API_KEY=your_key
EMBEDDING_BASE_URL=http://your-embedding-server:9997/v1
EMBEDDING_DIMENSION=1024

# Reranker 服务配置（可选，用于精排）
RERANK_ENABLED=true
RERANK_PROVIDER=custom
RERANK_BASE_URL=http://your-reranker-server:9997/v1
RERANK_ENDPOINT=/rerank         # 重要：必须配置，不能为空
RERANK_MODEL=bge-reranker-large
RERANK_API_KEY=your_key

# 数据库配置
PGHOST=postgres
PGPORT=5432
PGDATABASE=vector_db
PGUSER=postgres
PGPASSWORD=postgres

# 处理模式
USE_LLM=true                    # 启用 LLM 文本重写
LLM_FALLBACK_TO_FLATTEN=false   # LLM 失败时回退到扁平化模式
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

**服务地址**
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- PostgreSQL: localhost:5432

**健康检查**
```bash
curl http://localhost:8000/health
# 返回: {"status":"ok"}
```

## 使用指南

### 数据接入

#### 方式一：Excel 文件导入

**1. 准备数据**

将 Excel 文件放入 `data/` 目录。系统支持：
- 多 sheet 自动处理
- 自动字段检测
- 中文列名支持

**2. 发起导入请求（全量模式）**

```bash
curl -X POST http://localhost:8000/api/ingest/excel \
  -H "Content-Type: application/json" \
  -d '{
    "excel_path": "/app/data/企业数据.xlsx",
    "incremental": false
  }'
```

**返回示例**
```json
{
  "message": "ingest started",
  "path": "/app/data/企业数据.xlsx",
  "mode": "full"
}
```

**3. 发起导入请求（增量模式，推荐）**

```bash
curl -X POST http://localhost:8000/api/ingest/excel \
  -H "Content-Type: application/json" \
  -d '{
    "excel_path": "/app/data/企业数据.xlsx",
    "incremental": true
  }'
```

增量模式优势：
- 自动检测内容变化
- 只处理修改的行
- 大幅降低 LLM/Embedding 调用成本（节省 95%+）

**处理流程**
1. 读取所有 sheet 和行
2. 对每行数据：
   - 增量模式：计算内容哈希，对比数据库，跳过未修改的行
   - 全量模式：处理所有行
3. LLM 重写为自然语言（或使用扁平化模式）
4. 调用 Embedding API 生成向量
5. 存入 pgvector 数据库

#### 方式二：MySQL 表导入

**发起导入请求**

```bash
curl -X POST http://localhost:8000/api/ingest/mysql \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "mysql+pymysql://user:password@host:3306/database",
    "table": "users",
    "mode": "rewrite",
    "id_column": "user_id",
    "where": "status = '\''active'\''",
    "limit": 1000
  }'
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_url | string | 是 | MySQL 连接字符串 |
| table | string | 是 | 表名 |
| mode | string | 否 | 处理模式：rewrite（LLM重写）/ flatten（扁平化），默认 rewrite |
| id_column | string | 否 | 主键列名，默认使用行索引 |
| where | string | 否 | SQL WHERE 条件 |
| limit | integer | 否 | 限制处理行数 |
| company_field | string | 否 | 企业名称字段名 |
| report_year_field | string | 否 | 报告年份字段名 |

**返回示例**
```json
{
  "message": "ingest started",
  "table": "users"
}
```

**后台处理流程**
1. 连接 MySQL 数据库
2. 读取表结构和数据
3. LLM 重写或扁平化处理
4. 生成向量
5. 存入向量数据库

### 数据查询

#### 查看已导入数据

```bash
# 方式 1: 使用 psql
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT source_table, COUNT(*) as count
FROM searchable_documents
GROUP BY source_table;
"
```

**输出示例**
```
 source_table | count
--------------+-------
 企业信息     |   150
 企业专利     |    89
 政策数据     |    20
```

```bash
# 方式 2: 查看具体内容
docker exec temp30_postgres_1 psql -U postgres -d vector_db -c "
SELECT
  id,
  source_table,
  source_id,
  LEFT(content, 100) as content_preview,
  jsonb_pretty(metadata) as metadata
FROM searchable_documents
WHERE source_table = '企业信息'
LIMIT 2;
"
```

**输出示例**
```
 id | source_table | source_id | content_preview | metadata
----+--------------+-----------+-----------------+-----------
  1 | 企业信息     | 0         | 常州市城投建...  | {
    |              |           |                 |   "企业名称": "常州市城投建设工程招标有限公司",
    |              |           |                 |   "统一社会信用代码": "91320411338771865Y",
    |              |           |                 |   "注册资本": "100万元"
    |              |           |                 | }
```

### 向量检索（召回）

#### 基础向量检索

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能相关的政策支持",
    "top_k": 5,
    "threshold": 0.5,
    "source_tables": ["政策数据"]
  }'
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 查询文本 |
| top_k | integer | 否 | 返回结果数量，默认 5 |
| threshold | float | 否 | 相似度阈值（0-1），默认 null |
| metric | string | 否 | 距离度量：cosine / l2，默认 cosine |
| source_tables | array | 否 | 限定查询的表名列表 |
| company_filter | string | 否 | 按企业名称过滤 |

**返回示例**
```json
{
  "query": "人工智能相关的政策支持",
  "results": [
    {
      "id": 125,
      "source_table": "政策数据",
      "source_id": "3",
      "content": "《关于促进人工智能产业发展的若干政策》旨在支持AI技术创新...",
      "similarity": 0.7823,
      "distance": 0.2177,
      "metadata": {
        "政策名称": "关于促进人工智能产业发展的若干政策",
        "政策级别": "市级",
        "发布时间": "2024-01-15"
      }
    },
    {
      "id": 87,
      "source_table": "政策数据",
      "source_id": "12",
      "content": "《智能制造专项扶持资金管理办法》明确对采用AI技术的企业...",
      "similarity": 0.7234,
      "distance": 0.2766,
      "metadata": {
        "政策名称": "智能制造专项扶持资金管理办法",
        "政策级别": "区级",
        "发布时间": "2023-11-20"
      }
    }
  ],
  "count": 2
}
```

#### 混合召回检索（推荐）

混合召回结合向量检索和 Rerank 精排，提供更高质量的结果。

```bash
curl -X POST http://localhost:8000/api/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "新能源汽车产业扶持政策",
    "vector_top_k": 20,
    "rerank_top_k": 10,
    "source_tables": ["政策数据"]
  }'
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 查询文本 |
| vector_top_k | integer | 否 | 向量检索召回数量，默认 20 |
| rerank_top_k | integer | 否 | 精排后返回数量，默认 10 |
| threshold | float | 否 | 相似度阈值 |
| source_tables | array | 否 | 限定查询的表名列表 |

**返回示例**
```json
{
  "query": "新能源汽车产业扶持政策",
  "results": [
    {
      "id": 45,
      "source_table": "政策数据",
      "content": "《新能源汽车产业发展专项资金使用管理办法》...",
      "similarity": 0.8234,
      "rerank_score": 0.9512,
      "metadata": {...}
    }
  ],
  "count": 10
}
```

**字段说明**
- `similarity`: 向量余弦相似度（0-1，越高越相似）
- `rerank_score`: Rerank模型打分（0-1，越高越相关）
- 最终排序优先使用 `rerank_score`，回退到 `similarity`

**召回流程**
1. **向量检索**：先召回 vector_top_k (如20个) 个相似候选
2. **Rerank 精排**：对候选结果使用专门的重排序模型精排，返回 rerank_top_k (如10个) 个高质量结果
3. **混合策略**：
   - 如果向量和Rerank结果有交集：返回交集部分（按Rerank分数排序）
   - 如果没有交集：仅返回Rerank精排结果
   - 如果Rerank失败或未启用：返回向量检索结果

### 跨表联合查询

系统支持同时检索多个数据源：

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "常州纳欧新材料科技有限公司",
    "top_k": 10,
    "source_tables": ["企业信息", "企业专利", "企业融资信息", "政策数据"]
  }'
```

返回结果将包含该企业在不同表中的所有相关信息。

## 数据库结构

### 核心表：searchable_documents

```sql
CREATE TABLE searchable_documents (
    id BIGSERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,        -- 数据来源表名
    source_id TEXT NOT NULL,           -- 原始记录ID
    content TEXT NOT NULL,             -- 处理后的可搜索文本
    embedding vector(1024),            -- 1024维向量
    metadata JSONB,                    -- 原始数据（JSON格式）
    content_hash TEXT,                 -- 内容哈希（用于增量更新）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_name TEXT,                 -- 企业名称（可选）
    report_year TEXT,                  -- 报告年份（可选）
    credit_no TEXT,                    -- 信用代码（可选）
    origin_status TEXT,                -- 原始状态（可选）
    UNIQUE(source_table, source_id)
);

-- 索引
CREATE UNIQUE INDEX idx_sd_source_pair ON searchable_documents(source_table, source_id);
CREATE INDEX idx_metadata ON searchable_documents USING GIN (metadata);
CREATE INDEX idx_content_hash ON searchable_documents(source_table, source_id, content_hash);
```

**字段说明**
- `source_table`：区分不同的数据源（如：企业信息、政策数据）
- `source_id`：原始数据的唯一标识
- `content`：经过 LLM 重写或扁平化处理的文本，用于展示和分析
- `embedding`：文本的向量表示，用于语义检索
- `metadata`：完整的原始数据，以 JSON 格式存储，支持灵活查询
- `content_hash`：内容的 MD5 哈希值，用于增量更新时检测变化

### JSONB 元数据查询

```sql
-- 提取特定字段
SELECT
    content,
    metadata->>'企业名称' as company,
    metadata->>'注册资本' as capital,
    metadata->>'成立日期' as founded_date
FROM searchable_documents
WHERE source_table = '企业信息';

-- 按 JSON 字段筛选
SELECT * FROM searchable_documents
WHERE metadata->>'行业' = '人工智能'
  AND (metadata->>'注册资本')::numeric > 1000;

-- JSON 数组查询
SELECT * FROM searchable_documents
WHERE metadata->'股东信息' @> '[{"name": "张三"}]';
```

## 处理模式对比

### Flatten 模式（快速模式）

**特点**
- 直接拼接所有字段为 key-value 格式
- 处理速度快，无 LLM 调用成本
- 适合字段规范、可读性强的结构化数据

**示例输入**
```json
{
  "user_id": 1001,
  "username": "张三",
  "email": "zhangsan@example.com",
  "age": 28
}
```

**处理结果**
```
user_id: 1001 | username: 张三 | email: zhangsan@example.com | age: 28
```

**配置**
```bash
# .env 配置
USE_LLM=false

# 或 API 调用时指定
{
  "mode": "flatten"
}
```

### LLM Rewrite 模式（推荐模式）

**特点**
- 使用 LLM 将结构化数据重写为自然语言
- 文本可读性高，检索效果优
- 适合需要高质量语义检索的场景

**示例输入**
```json
{
  "政策名称": "关于促进产业高质量发展的若干政策",
  "政策级别": "市级",
  "适用范围": "常州市区",
  "主要内容": "五年内安排500亿元政策性资金撬动8000亿元社会资本..."
}
```

**处理结果**
```
《关于促进产业高质量发展的若干政策》是常州市级政策，适用于常州市区范围。
该政策旨在全面落实"532"发展战略，通过五年内安排500亿元政策性资金撬动
8000亿元社会资本，重点支持产业升级和创新体系建设...
```

**配置**
```bash
# .env 配置
USE_LLM=true
LLM_FALLBACK_TO_FLATTEN=false

# 或 API 调用时指定
{
  "mode": "rewrite"
}
```

## 自定义 Prompt（高级功能）

为不同业务表定制专门的 Prompt 模板，提升文本重写质量。

**1. 创建 Prompt 配置文件**

`prompts/custom.json`
```json
{
  "企业信息": {
    "system": "你是一名企业分析专家，擅长总结企业基本情况。",
    "user": "请用一段话描述以下企业的基本信息：\n${row_flat}\n\n要求：突出企业名称、行业、注册资本、成立时间等关键信息，语言简洁专业。"
  },
  "政策数据": {
    "system": "你是一名政策分析专家，擅长解读政府政策文件。",
    "user": "请总结以下政策的核心内容：\n${row_flat}\n\n要求：说明政策名称、级别、主要措施和支持范围，语言专业准确。"
  },
  "企业专利": {
    "system": "你是一名知识产权分析师，擅长描述专利信息。",
    "user": "请描述以下专利的要点：\n${row_flat}\n\n要求：包含专利名称、申请人、申请日期、技术领域等关键信息。"
  }
}
```

**2. 配置环境变量**

`.env`
```bash
PROMPT_CONFIG_PATH=prompts/custom.json
```

**3. 重启服务**

```bash
docker-compose restart api
```

**模板变量说明**
- `${row_flat}`: 自动插入当前行的扁平化文本
- 可在 system 和 user 字段中使用任意文本

## 常见问题

### 1. 如何查看处理进度？

```bash
# 查看实时日志
docker-compose logs -f api

# 查看最近 50 行日志
docker-compose logs --tail=50 api
```

### 2. 如何处理大量数据？

建议分批处理：
```bash
# 限制每次处理 1000 条
curl -X POST http://localhost:8000/api/ingest/mysql \
  -d '{
    "table": "large_table",
    "limit": 1000,
    "where": "id > 0 AND id <= 1000"
  }'

# 再处理下一批
curl -X POST http://localhost:8000/api/ingest/mysql \
  -d '{
    "table": "large_table",
    "limit": 1000,
    "where": "id > 1000 AND id <= 2000"
  }'
```

### 3. 如何更新已导入的数据？

使用增量模式：
```bash
curl -X POST http://localhost:8000/api/ingest/excel \
  -d '{
    "excel_path": "/app/data/企业数据.xlsx",
    "incremental": true
  }'
```

系统会自动：
- 检测内容变化
- 只处理修改的行
- 跳过未修改的数据

### 4. 如何删除某个表的数据？

```sql
-- 连接数据库
docker exec -it temp30_postgres_1 psql -U postgres -d vector_db

-- 删除指定表的数据
DELETE FROM searchable_documents WHERE source_table = '表名';
```

### 5. 内网 LLM 服务不稳定怎么办？

启用回退机制：
```bash
# .env 配置
LLM_FALLBACK_TO_FLATTEN=true
```

LLM 多次失败后自动切换为扁平化模式，确保流程继续执行。

### 6. Rerank 服务返回 500 错误怎么办？

检查配置：
```bash
# 确保 RERANK_ENDPOINT 已配置
RERANK_ENDPOINT=/rerank  # 不能为空

# 检查完整URL是否正确
# 最终请求: {RERANK_BASE_URL}{RERANK_ENDPOINT}
# 例如: http://10.168.2.250:9997/v1/rerank
```

常见问题：
- ❌ `RERANK_ENDPOINT=` （空值会导致404）
- ✅ `RERANK_ENDPOINT=/rerank`
- ❌ 请求发送dict数组（老版本bug）
- ✅ 请求发送字符串数组

### 7. 如何配置代理？

如果 Embedding/LLM 服务在内网，需要配置代理例外：
```bash
export NO_PROXY="localhost,127.0.0.1,10.168.2.110,10.168.2.250"
export no_proxy="localhost,127.0.0.1,10.168.2.110,10.168.2.250"
```

## 性能优化建议

### 1. 批量处理优化

```bash
# .env 中配置批量大小
BATCH_SIZE=32  # embedding 批量大小
```

### 2. 数据库性能

```sql
-- 定期清理和分析表
VACUUM ANALYZE searchable_documents;

-- 创建额外索引（根据查询需求）
CREATE INDEX idx_company ON searchable_documents(company_name);
CREATE INDEX idx_year ON searchable_documents(report_year);
```

### 3. 增量更新

对于频繁更新的数据源，始终使用增量模式以降低成本：
```bash
{
  "incremental": true
}
```

## API 接口完整文档

启动服务后访问 Swagger 文档：http://localhost:8000/docs

**主要接口**

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ingest/excel` | POST | Excel 文件导入 |
| `/api/ingest/mysql` | POST | MySQL 表导入 |
| `/api/search` | POST | 向量检索 |
| `/api/search/hybrid` | POST | 混合召回检索 |
| `/health` | GET | 健康检查 |

## Docker 部署

### 服务组成

- **postgres**: pgvector 向量数据库
- **api**: FastAPI 应用服务

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart api

# 查看日志
docker-compose logs -f api

# 进入容器
docker-compose exec api bash

# 查看资源使用
docker stats
```

### 数据持久化

数据存储在 Docker 卷中：
```bash
# 查看卷
docker volume ls | grep temp30

# 备份数据
docker exec temp30_postgres_1 pg_dump -U postgres vector_db > backup.sql

# 恢复数据
docker exec -i temp30_postgres_1 psql -U postgres vector_db < backup.sql
```

## 技术栈

- **API 框架**: FastAPI
- **向量数据库**: PostgreSQL + pgvector
- **LLM**: 通用 OpenAI 兼容接口
- **Embedding**: 通用 OpenAI 兼容接口
- **Rerank**: 自定义重排序服务
- **容器化**: Docker + Docker Compose

## 许可证

请根据公司要求添加许可证信息。

## 技术支持

如有问题请联系技术支持团队。

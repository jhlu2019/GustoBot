# ChatDB - 智能数据库对话系统

## 📖 项目简介

ChatDB 是一个基于大语言模型（LLM）的智能 Text2SQL 系统，允许用户通过自然语言查询数据库，并自动生成可视化图表。系统采用多智能体架构，结合图数据库进行表关系管理，提供企业级的自然语言到 SQL 的转换能力。

### 核心特性

- 🤖 **多智能体协作**：采用 Microsoft AutoGen 框架，6 个专门智能体协同工作
- 📊 **智能可视化**：自动分析查询结果并推荐最佳可视化方式（柱状图、折线图、饼图、散点图等）
- 🔗 **图数据库管理**：使用 Neo4j 存储表关系，智能理解表之间的关联
- 💡 **语义理解**：支持自然语言术语到数据库值的映射（如"中石化" → "中国石化"）
- ⚡ **实时流式响应**：通过 SSE（Server-Sent Events）实时反馈处理进度
- 🔍 **混合检索增强**：可选的向量检索（Milvus）+ 结构化检索混合模式

---

## 🏗️ 系统架构

### 技术栈

| 组件 | 技术 | 作用 |
|------|------|------|
| **后端框架** | FastAPI | RESTful API + SSE 流式接口 |
| **ORM** | SQLAlchemy | 数据库操作与模型管理 |
| **元数据存储** | MySQL | 存储连接配置、表结构、字段映射 |
| **关系图谱** | Neo4j | 存储表关系图，支持智能 Schema 检索 |
| **LLM** | DeepSeek Chat | 通过 OpenAI 兼容接口调用 |
| **智能体框架** | AutoGen | 多智能体编排与通信 |
| **向量数据库** | Milvus (可选) | 语义检索增强 |
| **嵌入模型** | BGE-small-zh | 中文向量嵌入 |

### 数据库表结构

系统使用 MySQL 存储以下元数据：

#### 1. **DBConnection** - 数据库连接
```sql
CREATE TABLE dbconnection (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,      -- 连接名称
    db_type VARCHAR(50) NOT NULL,           -- 数据库类型 (mysql, postgresql 等)
    host VARCHAR(255) NOT NULL,             -- 主机地址
    port INT NOT NULL,                      -- 端口
    username VARCHAR(255) NOT NULL,         -- 用户名
    password_encrypted VARCHAR(255) NOT NULL, -- 加密后的密码
    database_name VARCHAR(255) NOT NULL,    -- 数据库名
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

#### 2. **SchemaTable** - 表元数据
```sql
CREATE TABLE schematable (
    id INT PRIMARY KEY AUTO_INCREMENT,
    connection_id INT NOT NULL,             -- 关联的连接 ID
    table_name VARCHAR(255) NOT NULL,       -- 表名
    description TEXT,                       -- 表描述（业务含义）
    ui_metadata JSON,                       -- UI 配置（如位置坐标）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES dbconnection(id)
);
```

#### 3. **SchemaColumn** - 字段元数据
```sql
CREATE TABLE schemacolumn (
    id INT PRIMARY KEY AUTO_INCREMENT,
    table_id INT NOT NULL,                  -- 关联的表 ID
    column_name VARCHAR(255) NOT NULL,      -- 字段名
    data_type VARCHAR(100) NOT NULL,        -- 数据类型
    description TEXT,                       -- 字段描述
    is_primary_key BOOLEAN DEFAULT FALSE,   -- 是否主键
    is_foreign_key BOOLEAN DEFAULT FALSE,   -- 是否外键
    is_unique BOOLEAN DEFAULT FALSE,        -- 是否唯一
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES schematable(id)
);
```

#### 4. **SchemaRelationship** - 表关系
```sql
CREATE TABLE schemarelationship (
    id INT PRIMARY KEY AUTO_INCREMENT,
    connection_id INT NOT NULL,
    source_table_id INT NOT NULL,           -- 源表
    source_column_id INT NOT NULL,          -- 源字段
    target_table_id INT NOT NULL,           -- 目标表
    target_column_id INT NOT NULL,          -- 目标字段
    relationship_type VARCHAR(50),          -- 关系类型 (1-to-1, 1-to-N, N-to-M)
    description TEXT,                       -- 关系描述
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES dbconnection(id),
    FOREIGN KEY (source_table_id) REFERENCES schematable(id),
    FOREIGN KEY (target_table_id) REFERENCES schematable(id),
    FOREIGN KEY (source_column_id) REFERENCES schemacolumn(id),
    FOREIGN KEY (target_column_id) REFERENCES schemacolumn(id)
);
```

#### 5. **ValueMapping** - 值映射
```sql
CREATE TABLE valuemapping (
    id INT PRIMARY KEY AUTO_INCREMENT,
    column_id INT NOT NULL,                 -- 关联的字段 ID
    nl_term VARCHAR(255) NOT NULL,          -- 自然语言术语（如"中石化"）
    db_value VARCHAR(255) NOT NULL,         -- 数据库实际值（如"中国石化"）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (column_id) REFERENCES schemacolumn(id)
);
```

#### 6. **ChatSession / ChatMessage** - 对话历史
```sql
CREATE TABLE chatsession (
    id INT PRIMARY KEY AUTO_INCREMENT,
    connection_id INT NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES dbconnection(id)
);

CREATE TABLE chatmessage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,              -- user / assistant
    content TEXT NOT NULL,
    sql TEXT,                               -- 生成的 SQL（如果有）
    results JSON,                           -- 查询结果（如果有）
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES chatsession(id)
);
```

---

## 🔄 Text2SQL 完整流程

### 整体流程图

```
┌─────────────────────────────────────────────────────────────────┐
│  用户输入自然语言查询："查询中石化去年的销售额"                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. SchemaRetrieverAgent - Schema 检索智能体                     │
├─────────────────────────────────────────────────────────────────┤
│  • 从 Neo4j 查询相关表结构（基于关键词 + LLM 语义匹配）            │
│  • 获取表的字段信息（companies, sales 等）                        │
│  • 获取值映射（"中石化" → "中国石化"）                            │
│  • 自动扩展关联表（通过外键关系）                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │  Schema Context + Value Mappings     │
          │  {                                   │
          │    tables: [companies, sales],       │
          │    columns: [...],                   │
          │    relationships: [...],             │
          │    value_mappings: {                 │
          │      "company.name": {               │
          │        "中石化": "中国石化"           │
          │      }                                │
          │    }                                 │
          │  }                                   │
          └──────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. QueryAnalyzerAgent - 查询分析智能体                          │
├─────────────────────────────────────────────────────────────────┤
│  • 使用 LLM 分析用户意图                                         │
│  • 识别需要的表和字段                                            │
│  • 确定连接关系、筛选条件、聚合方式                               │
│  • 生成结构化的 SQL 分析报告                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │  SQL 分析报告                         │
          │  {                                   │
          │    "查询意图": "统计销售额",          │
          │    "需要的表": ["companies", "sales"],│
          │    "连接方式": "sales.company_id =   │
          │                companies.id",        │
          │    "筛选条件": "company.name='中国石化'│
          │                AND year=2024",       │
          │    "聚合操作": "SUM(amount)"          │
          │  }                                   │
          └──────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SqlGeneratorAgent - SQL 生成智能体                           │
├─────────────────────────────────────────────────────────────────┤
│  • 根据分析报告生成精确 SQL                                       │
│  • Temperature = 0.1（确保输出确定性）                            │
│  • 仅输出纯 SQL，无额外解释                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │  生成的 SQL                           │
          │  SELECT SUM(s.amount) as total       │
          │  FROM sales s                        │
          │  JOIN companies c                    │
          │    ON s.company_id = c.id            │
          │  WHERE c.name = '中国石化'            │
          │    AND s.sale_date >= '2024-01-01'   │
          │    AND s.sale_date < '2025-01-01'    │
          └──────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. SQL 验证与执行                                               │
├─────────────────────────────────────────────────────────────────┤
│  • 提取 SQL（去除 markdown 标记）                                │
│  • 应用值映射（确保术语正确）                                     │
│  • 验证 SQL 语法（使用 sqlparse）                                │
│  • 执行查询并返回结果                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │  查询结果                             │
          │  [                                   │
          │    {"total": 1000000000}             │
          │  ]                                   │
          └──────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. SqlExplainerAgent - SQL 解释智能体                           │
├─────────────────────────────────────────────────────────────────┤
│  • 用自然语言解释 SQL 的含义                                      │
│  • "这条 SQL 查询了中国石化公司在 2024 年的总销售额"              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. VisualizationRecommenderAgent - 可视化推荐智能体              │
├─────────────────────────────────────────────────────────────────┤
│  • 分析查询结果的数据结构                                         │
│  • 推荐最佳可视化类型（bar/line/pie/scatter/table）               │
│  • 生成可视化配置（坐标轴、系列名称等）                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │  可视化配置                           │
          │  {                                   │
          │    "type": "bar",                    │
          │    "config": {                       │
          │      "title": "中石化 2024 销售额",   │
          │      "xAxis": "company",             │
          │      "yAxis": "total"                │
          │    }                                 │
          │  }                                   │
          └──────────────┬───────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  返回给前端：SQL + 结果 + 解释 + 可视化配置                        │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流示例

**用户问题**：
```
"查询中石化去年的销售额"
```

**1. Schema 检索结果**：
```json
{
  "tables": [
    {
      "table_name": "companies",
      "columns": [
        {"column_name": "id", "data_type": "INT"},
        {"column_name": "name", "data_type": "VARCHAR(100)"}
      ]
    },
    {
      "table_name": "sales",
      "columns": [
        {"column_name": "id", "data_type": "INT"},
        {"column_name": "company_id", "data_type": "INT"},
        {"column_name": "amount", "data_type": "DECIMAL"},
        {"column_name": "sale_date", "data_type": "DATE"}
      ]
    }
  ],
  "value_mappings": {
    "companies.name": {
      "中石化": "中国石化"
    }
  }
}
```

**2. 发送给 LLM 的 Prompt**：
```
你是专业的 SQL 开发专家...

### 数据库结构:
-- companies 表
CREATE TABLE companies (
  id INT,
  name VARCHAR(100)
);

-- sales 表
CREATE TABLE sales (
  id INT,
  company_id INT,
  amount DECIMAL,
  sale_date DATE
);

### 值映射:
-- 对于 companies.name:
--   自然语言中的'中石化'指数据库中的'中国石化'

### 自然语言问题:
"查询中石化去年的销售额"

### 指令:
1. 分析问题并识别相关的表和列
2. 考虑表之间的关系
3. 生成有效的 SQL 查询
...
```

**3. LLM 返回的 SQL**：
```sql
SELECT SUM(s.amount) as total_sales
FROM sales s
JOIN companies c ON s.company_id = c.id
WHERE c.name = '中国石化'
  AND s.sale_date >= '2024-01-01'
  AND s.sale_date < '2025-01-01'
```

**4. 执行结果**：
```json
[
  {"total_sales": 1000000000}
]
```

**5. 最终返回**：
```json
{
  "sql": "SELECT SUM(s.amount) as total_sales...",
  "explanation": "这条 SQL 查询了中国石化公司在 2024 年的总销售额",
  "results": [{"total_sales": 1000000000}],
  "visualization_type": "bar",
  "visualization_config": {
    "title": "中石化 2024 销售额",
    "xAxis": "company",
    "yAxis": "total_sales"
  }
}
```

---

## 🚀 快速开始

### 前置要求

- Python 3.9+
- MySQL 5.7+
- Neo4j 4.0+
- OpenAI API Key（或 DeepSeek API Key）

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd chatdb/backend
```

#### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
编辑 `.env` 文件：
```bash
# OpenAI 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.deepseek.com/v1  # 可选，使用 DeepSeek
LLM_MODEL=deepseek-chat

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# MySQL 配置
MYSQL_SERVER=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DB=chatdb

# Milvus 配置（可选）
MILVUS_HOST=localhost
MILVUS_PORT=19530
HYBRID_RETRIEVAL_ENABLED=false  # 关闭混合检索
```

#### 5. 创建数据库
```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE chatdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 6. 初始化数据库表
```bash
python init_db.py
```

这会创建所有必需的表（dbconnection, schematable, schemacolumn 等）。

#### 7. 启动服务
```bash
python main.py
# 或者
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

---

## 📘 使用指南

### 1. 创建数据库连接

**API**: `POST /api/connections`

```json
{
  "name": "我的MySQL数据库",
  "db_type": "mysql",
  "host": "localhost",
  "port": 3306,
  "username": "root",
  "password": "password",
  "database_name": "your_database"
}
```

### 2. 发现并同步表结构

**API**: `POST /api/schema/{connection_id}/discover-and-sync`

这个操作会：
1. 自动扫描数据库中的所有表和字段
2. 识别主键、外键、唯一约束
3. 分析表之间的关系
4. 将结构同步到 MySQL 元数据库
5. 将表关系图谱同步到 Neo4j

### 3. 添加表和字段的业务描述

**API**: `PUT /api/schema/tables/{table_id}`

```json
{
  "description": "公司基本信息表，包含公司名称、注册信息等"
}
```

**API**: `PUT /api/schema/columns/{column_id}`

```json
{
  "description": "公司名称，存储公司全称"
}
```

### 4. 配置值映射

**API**: `POST /api/value-mappings`

```json
{
  "column_id": 123,
  "nl_term": "中石化",
  "db_value": "中国石化"
}
```

### 5. 执行 Text2SQL 查询

**API**: `POST /api/text2sql/stream`（SSE 流式接口）

```json
{
  "connection_id": 1,
  "query": "查询中石化去年的销售额"
}
```

**响应**（SSE 事件流）：
```
event: message
data: {"agent": "schema_retriever", "content": "正在检索相关表结构..."}

event: message
data: {"agent": "query_analyzer", "content": "分析查询意图..."}

event: sql
data: {"sql": "SELECT SUM(amount)..."}

event: data
data: {"results": [{"total_sales": 1000000000}]}

event: visualization
data: {"type": "bar", "config": {...}}

event: complete
data: {"status": "success"}
```

---

## 🔧 核心 API 接口

### 连接管理
- `GET /api/connections` - 获取所有连接
- `POST /api/connections` - 创建新连接
- `PUT /api/connections/{id}` - 更新连接
- `DELETE /api/connections/{id}` - 删除连接

### Schema 管理
- `GET /api/schema/{connection_id}/discover` - 发现表结构
- `GET /api/schema/{connection_id}/metadata` - 获取元数据
- `POST /api/schema/{connection_id}/publish` - 发布 Schema 到 MySQL + Neo4j
- `POST /api/schema/{connection_id}/sync-to-neo4j` - 同步到 Neo4j
- `POST /api/schema/{connection_id}/discover-and-sync` - 一键发现并同步

### 值映射
- `GET /api/value-mappings/column/{column_id}` - 获取字段的映射
- `POST /api/value-mappings` - 创建映射
- `PUT /api/value-mappings/{id}` - 更新映射
- `DELETE /api/value-mappings/{id}` - 删除映射

### Text2SQL
- `POST /api/text2sql/stream` - SSE 流式查询（推荐）
- `POST /api/text2sql` - 普通查询（已废弃）

### 对话历史
- `GET /api/chat-history/sessions` - 获取会话列表
- `POST /api/chat-history/sessions` - 创建会话
- `GET /api/chat-history/sessions/{session_id}/messages` - 获取消息

---

## 📂 项目结构

```
chatdb/backend/
├── app/
│   ├── agents/                    # 智能体模块
│   │   ├── base.py               # 基础智能体类
│   │   ├── schema_retriever.py   # Schema 检索智能体
│   │   ├── query_analyzer.py     # 查询分析智能体
│   │   ├── sql_generator.py      # SQL 生成智能体
│   │   ├── sql_explainer.py      # SQL 解释智能体
│   │   ├── sql_executor.py       # SQL 执行智能体
│   │   └── visualization_recommender.py  # 可视化推荐智能体
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/        # API 端点
│   │           ├── connections.py    # 连接管理
│   │           ├── schema.py         # Schema 管理
│   │           ├── value_mappings.py # 值映射
│   │           ├── text2sql_sse.py   # Text2SQL SSE 接口
│   │           └── chat_history.py   # 对话历史
│   ├── core/                     # 核心配置
│   │   ├── config.py            # 环境配置
│   │   └── llms.py              # LLM 客户端
│   ├── crud/                     # CRUD 操作
│   ├── db/                       # 数据库配置
│   ├── models/                   # SQLAlchemy 模型
│   │   ├── db_connection.py     # 连接模型
│   │   ├── schema_table.py      # 表模型
│   │   ├── schema_column.py     # 字段模型
│   │   ├── schema_relationship.py # 关系模型
│   │   └── value_mapping.py     # 值映射模型
│   ├── schemas/                  # Pydantic Schema
│   └── services/                 # 业务逻辑
│       ├── schema_service.py    # Schema 服务
│       ├── text2sql_service.py  # Text2SQL 服务
│       └── text2sql_utils.py    # Text2SQL 工具函数
├── alembic/                      # 数据库迁移
├── .env                          # 环境变量
├── requirements.txt              # 依赖列表
├── init_db.py                    # 数据库初始化脚本
└── main.py                       # 应用入口
```

---

## 🔍 关键实现细节

### 1. Schema 自动发现

**文件**: `app/services/schema_service.py:discover_schema()`

```python
def discover_schema(connection: DBConnection):
    """自动发现数据库 Schema"""
    # 1. 连接目标数据库
    # 2. 使用 SQLAlchemy 反射获取表结构
    # 3. 分析外键关系
    # 4. 识别主键、唯一约束
    # 5. 返回结构化的 Schema 信息
```

### 2. 同步到 Neo4j

**文件**: `app/services/schema_service.py:sync_schema_to_graph_db()`

```python
def sync_schema_to_graph_db(connection_id: int):
    """将 Schema 同步到 Neo4j 图数据库"""
    # 1. 清除旧的图谱数据
    # 2. 创建 Table 节点
    # 3. 创建 Column 节点
    # 4. 创建表之间的 RELATES_TO 关系
    # 5. 创建字段之间的 HAS_COLUMN 关系
```

Neo4j 中的图结构：
```
(Table:companies) -[HAS_COLUMN]-> (Column:id)
(Table:companies) -[HAS_COLUMN]-> (Column:name)
(Table:sales) -[HAS_COLUMN]-> (Column:company_id)
(Table:sales) -[RELATES_TO {via: "company_id"}]-> (Table:companies)
```

### 3. 智能 Schema 检索

**文件**: `app/services/text2sql_utils.py:retrieve_relevant_schema()`

检索策略：
1. **关键词匹配**：从用户问题中提取关键词，匹配表名和字段名
2. **语义匹配**：使用 LLM 分析问题，语义化匹配表的业务描述
3. **关系扩展**：通过 Neo4j 图遍历，自动包含关联表
4. **值映射加载**：加载相关字段的自然语言映射

### 4. Prompt 构造

**文件**: `app/services/text2sql_service.py:construct_prompt()`

Prompt 结构：
```
### 数据库结构:
[表结构的 CREATE TABLE 语句]

### 值映射:
[自然语言术语到数据库值的映射]

### 自然语言问题:
[用户的问题]

### 指令:
1. 分析问题...
2. 生成 SQL...
```

### 5. 多智能体通信

**文件**: `app/agents/`

使用 AutoGen 的消息订阅机制：
```python
@type_subscription(topic_type=TopicTypes.SQL_GENERATOR.value)
class SqlGeneratorAgent(BaseAgent):
    @message_handler
    async def handle_analysis_message(self, message: AnalysisMessage, ctx: MessageContext):
        # 处理分析消息
        # 生成 SQL
        # 发布到下一个智能体
        await self.publish_message(sql_message, topic_id=...)
```

---

## 🎯 最佳实践

### 1. 提高查询准确性

✅ **添加详细的表和字段描述**
- 在 Schema 管理界面为每个表和字段添加业务含义
- 描述应该包含常见的业务术语

✅ **配置完整的值映射**
- 为重要字段配置常见的自然语言别名
- 例如：公司简称 → 公司全称

✅ **维护表关系**
- 确保外键关系正确同步到 Neo4j
- 手动补充系统未识别的业务关系

### 2. 优化性能

✅ **使用 Schema 缓存**
- 系统会缓存 Neo4j 查询结果
- 定期同步 Schema 而非每次查询时

✅ **限制表数量**
- 只同步业务相关的表
- 过滤掉系统表和临时表

### 3. 安全性

✅ **SQL 注入防护**
- 系统使用参数化查询
- LLM 生成的 SQL 会经过验证

✅ **只读查询**
- 默认只允许 SELECT 语句
- 可以在配置中限制 DML 操作

---

## 🐛 常见问题

### Q1: 生成的 SQL 不准确怎么办？

**A**:
1. 检查表和字段的描述是否完整
2. 添加相关的值映射
3. 确认表关系已同步到 Neo4j
4. 尝试更详细的问题描述

### Q2: Neo4j 连接失败

**A**:
```bash
# 检查 Neo4j 是否运行
systemctl status neo4j

# 检查防火墙
telnet your-neo4j-host 7687

# 检查 .env 中的配置
NEO4J_URI=bolt://localhost:7687
```

### Q3: LLM API 调用超时

**A**:
1. 检查 API Key 是否有效
2. 检查网络连接
3. 尝试增加 timeout 设置（在 `app/core/llms.py`）

### Q4: 查询结果为空

**A**:
1. 检查数据库连接是否正常
2. 验证 SQL 是否正确（查看返回的 SQL 字段）
3. 检查值映射是否生效
4. 手动执行生成的 SQL 验证

---

## 📊 数据初始化示例

### 示例 1: 销售数据库

```sql
-- 创建公司表
CREATE TABLE companies (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  industry VARCHAR(50)
);

-- 创建销售表
CREATE TABLE sales (
  id INT PRIMARY KEY AUTO_INCREMENT,
  company_id INT,
  amount DECIMAL(15,2),
  sale_date DATE,
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- 插入测试数据
INSERT INTO companies (name, industry) VALUES
  ('中国石化', '能源'),
  ('中国石油', '能源'),
  ('阿里巴巴', '互联网');

INSERT INTO sales (company_id, amount, sale_date) VALUES
  (1, 1000000, '2024-01-15'),
  (1, 1500000, '2024-06-20'),
  (2, 800000, '2024-03-10');
```

### 使用 ChatDB

1. 创建连接
2. 发现并同步 Schema
3. 添加值映射：
   - column: `companies.name`
   - nl_term: `中石化`
   - db_value: `中国石化`
4. 查询：
   - "查询中石化的销售额"
   - "2024年能源行业的总销售额是多少"
   - "对比各公司的销售额"

---

## 🚀 性能优化

### 1. Neo4j 索引

```cypher
// 为表名创建索引
CREATE INDEX table_name_index FOR (t:Table) ON (t.table_name);

// 为字段名创建索引
CREATE INDEX column_name_index FOR (c:Column) ON (c.column_name);
```

### 2. MySQL 索引

```sql
-- 表名索引（已在模型中定义）
CREATE INDEX idx_table_name ON schematable(table_name);

-- 字段映射索引
CREATE INDEX idx_nl_term ON valuemapping(nl_term);
```

### 3. 缓存策略

系统自动缓存：
- Schema 检索结果（TTL: 3600s）
- LLM 响应（相同问题）
- Neo4j 图谱查询

---

## 📝 开发指南

### 添加新的智能体

1. 在 `app/agents/` 创建新文件
2. 继承 `BaseAgent` 类
3. 定义消息处理器：
```python
@type_subscription(topic_type="YOUR_TOPIC")
class YourAgent(BaseAgent):
    @message_handler
    async def handle_message(self, message: YourMessage, ctx: MessageContext):
        # 处理逻辑
        pass
```

### 添加新的 API 端点

1. 在 `app/api/api_v1/endpoints/` 创建新文件
2. 定义路由：
```python
router = APIRouter()

@router.get("/your-endpoint")
def your_endpoint():
    return {"status": "ok"}
```
3. 在 `app/api/api_v1/api.py` 中注册路由

---

## 📄 许可证

[您的许可证信息]

---

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

[您的联系方式]

---

**祝你使用愉快！** 🎉

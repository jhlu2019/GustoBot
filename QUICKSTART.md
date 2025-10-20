# 🚀 GustoBot 快速开始

## 一键启动（LightRAG 自动初始化）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填写你的 OPENAI_API_KEY

# 2. 一键启动（自动构建并初始化 LightRAG）
docker-compose up -d

# 3. 查看日志（构建进度）
docker-compose logs -f server

# 4. 等待构建完成后访问
curl http://localhost:8000/api/v1/health
```

---

## ⚙️ 配置说明

### .env 文件（根目录）

从 `.env.example` 复制并修改：

```bash
# 必需：OpenAI API Key
OPENAI_API_KEY=sk-your-key-here

# 可选：是否构建时初始化 LightRAG
INIT_LIGHTRAG_ON_BUILD=true    # true=构建时初始化，false=跳过

# 可选：限制数量（测试用）
LIGHTRAG_INIT_LIMIT=           # 留空=全部，10=快速测试
```

**注意**：`.env` 文件应放在项目根目录（与 `docker-compose.yml` 同级）

---

## 📊 构建选项对比

| 配置 | 构建时间 | 镜像大小 | 启动时间 | 适用场景 |
|------|---------|---------|---------|---------|
| `INIT_LIGHTRAG_ON_BUILD=true` | ~15 分钟 | ~550MB | < 1 秒 | 🚀 生产环境 |
| `INIT_LIGHTRAG_ON_BUILD=true`<br>`LIGHTRAG_INIT_LIMIT=10` | ~3 分钟 | ~520MB | < 1 秒 | 🧪 快速测试 |
| `INIT_LIGHTRAG_ON_BUILD=false` | ~2 分钟 | ~500MB | 正常 | 💻 开发环境 |

---

## 🔍 验证初始化

### 检查 LightRAG 数据文件

```bash
# 查看生成的文件
docker-compose exec server ls -lh /app/data/lightrag/

# 预期输出：
# graph_chunk_entity_relation.graphml  (~15MB)
# kv_store_doc_status.json              (~100KB)
# kv_store_full_docs.json               (~25MB)
# kv_store_text_chunks.json             (~5MB)
# vdb_chunks.json                       (~2MB)
# vdb_entities.json                     (~1.5MB)
# vdb_relationships.json                (~1MB)
```

### 测试查询

```bash
docker-compose exec server python -c "
import asyncio
from app.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

async def test():
    api = LightRAGAPI()
    result = await api.query('红烧肉怎么做？', mode='hybrid')
    print(result['response'][:300])

asyncio.run(test())
"
```

---

## 🎯 使用场景

### 场景 1: 快速测试（推荐新手）

```bash
# .env 配置
OPENAI_API_KEY=sk-xxx
INIT_LIGHTRAG_ON_BUILD=true
LIGHTRAG_INIT_LIMIT=10         # 只处理 10 条数据

# 启动
docker-compose up -d

# 3 分钟后可用
```

### 场景 2: 完整部署（生产环境）

```bash
# .env 配置
OPENAI_API_KEY=sk-xxx
INIT_LIGHTRAG_ON_BUILD=true
LIGHTRAG_INIT_LIMIT=            # 处理全部数据

# 启动
docker-compose up -d

# 15 分钟后可用，之后启动 < 1 秒
```

### 场景 3: 开发模式（不初始化）

```bash
# .env 配置
OPENAI_API_KEY=sk-xxx
INIT_LIGHTRAG_ON_BUILD=false   # 跳过初始化

# 启动
docker-compose up -d

# 2 分钟后可用，镜像更小
```

---

## 🐛 常见问题

### Q1: 构建时报错 "OPENAI_API_KEY is not set"

**A**: 确保 `.env` 文件存在并包含正确的 API key

```bash
# 检查
cat .env | grep OPENAI_API_KEY

# 修正
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Q2: 构建太慢

**A**: 使用限制数量快速测试

```bash
# 在 .env 中设置
LIGHTRAG_INIT_LIMIT=10

# 重新构建
docker-compose build --no-cache server
docker-compose up -d
```

### Q3: 如何跳过 LightRAG 初始化？

**A**: 设置环境变量

```bash
# 在 .env 中设置
INIT_LIGHTRAG_ON_BUILD=false

# 重新构建
docker-compose up -d --build
```

### Q4: 如何查看构建进度？

**A**: 查看实时日志

```bash
# 构建时
docker-compose build server 2>&1 | grep -E "Initializing|INFO|成功|完成"

# 启动后
docker-compose logs -f server
```

---

## 📝 完整流程示例

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/GustoBot.git
cd GustoBot

# 2. 配置
cp .env.example .env
nano .env  # 填写 OPENAI_API_KEY

# 3. 快速测试（10 条数据）
echo "LIGHTRAG_INIT_LIMIT=10" >> .env
docker-compose up -d

# 4. 等待构建（约 3 分钟）
docker-compose logs -f server

# 5. 测试
curl http://localhost:8000/api/v1/health

# 6. 如果测试成功，完整构建
docker-compose down
sed -i 's/LIGHTRAG_INIT_LIMIT=10/LIGHTRAG_INIT_LIMIT=/g' .env
docker-compose up -d --build

# 7. 等待完整构建（约 15 分钟）
docker-compose logs -f server
```

---

## 🎉 总结

**只需两步**：

1. **配置**: `cp .env.example .env` 并填写 `OPENAI_API_KEY`
2. **启动**: `docker-compose up -d`

**Docker Compose 会自动**：
- ✅ 构建镜像
- ✅ 初始化 LightRAG
- ✅ 生成并打包 JSON 文件
- ✅ 启动所有服务

**就这么简单！** 🚀

# Docker Build 时初始化 LightRAG

## 🎯 目标

在 **Docker 构建时**自动运行 LightRAG 初始化，生成的 JSON 文件直接打包到镜像中，启动时即可使用。

---

## ✅ 优势

| 特性 | Docker Build 初始化 | 启动时初始化 |
|------|-------------------|-------------|
| **启动速度** | ⚡ 快速（数据已在镜像） | 🐌 慢（首次需初始化） |
| **镜像大小** | 📦 大（包含数据） | 📦 小 |
| **构建时间** | ⏱️ 长（需调用 API） | ⏱️ 短 |
| **数据一致性** | ✅ 一次构建，到处一致 | ⚠️ 每次启动可能不同 |
| **适用场景** | 🚀 生产环境 | 💻 开发环境 |

---

## 🚀 使用方法

### 方式 1: 使用构建脚本（推荐）

```bash
# 1. 配置 API key
echo "OPENAI_API_KEY=sk-your-key" > .env

# 2. 运行构建脚本
bash build-with-lightrag.sh

# 3. 启动服务
docker-compose up -d

# 4. 验证数据
docker-compose exec server ls -lh /app/data/lightrag/
```

**预期输出**:
```
========================================
Building Docker image with LightRAG
========================================
Init LightRAG: true
Limit: none
OpenAI Model: gpt-3.5-turbo
Embedding Model: text-embedding-3-small
========================================

[Docker build output...]

========================================
Initializing LightRAG during build...
========================================
INFO: 从 /app/data/recipe.json 加载菜谱数据...
INFO: ✓ 成功加载 1000 个菜谱
...
========================================
LightRAG initialization completed!
Generated files:
total 50M
-rw-r--r-- 1 root root  15M graph_chunk_entity_relation.graphml
-rw-r--r-- 1 root root 100K kv_store_doc_status.json
-rw-r--r-- 1 root root  25M kv_store_full_docs.json
-rw-r--r-- 1 root root 5.0M kv_store_text_chunks.json
-rw-r--r-- 1 root root 2.0M vdb_chunks.json
-rw-r--r-- 1 root root 1.5M vdb_entities.json
-rw-r--r-- 1 root root 1.0M vdb_relationships.json
========================================

✅ Build completed!
```

---

### 方式 2: 手动构建

```bash
# 完整构建（所有菜谱）
docker-compose build \
  --build-arg INIT_LIGHTRAG_ON_BUILD=true \
  --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
  server

# 测试构建（限制 10 条）
docker-compose build \
  --build-arg INIT_LIGHTRAG_ON_BUILD=true \
  --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
  --build-arg LIGHTRAG_INIT_LIMIT=10 \
  server
```

---

## ⚙️ 构建参数

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `INIT_LIGHTRAG_ON_BUILD` | 是否初始化 | `false` | ❌ |
| `OPENAI_API_KEY` | OpenAI API Key | - | ✅ |
| `OPENAI_API_BASE` | API 基础 URL | `https://api.openai.com/v1` | ❌ |
| `OPENAI_MODEL` | LLM 模型 | `gpt-3.5-turbo` | ❌ |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` | ❌ |
| `EMBEDDING_DIMENSION` | Embedding 维度 | `1536` | ❌ |
| `LIGHTRAG_INIT_LIMIT` | 限制数量 | 无限制 | ❌ |

---

## 📁 生成的文件

构建完成后，镜像中包含：

```
/app/data/lightrag/
├── graph_chunk_entity_relation.graphml   # 实体关系图（~15MB）
├── kv_store_doc_status.json              # 文档状态（~100KB）
├── kv_store_full_docs.json               # 完整文档（~25MB）
├── kv_store_text_chunks.json             # 文本块（~5MB）
├── vdb_chunks.json                       # 文本块向量（~2MB）
├── vdb_entities.json                     # 实体向量（~1.5MB）
└── vdb_relationships.json                # 关系向量（~1MB）
```

**总大小**: ~50MB

---

## 🔍 验证构建结果

### 1. 检查镜像大小

```bash
docker images | grep gustobot
```

应该看到镜像大小增加约 50MB（包含 LightRAG 数据）

### 2. 检查文件

```bash
# 启动临时容器检查
docker-compose run --rm server ls -lh /app/data/lightrag/

# 查看文档数量
docker-compose run --rm server python -c "
import json
with open('/app/data/lightrag/kv_store_doc_status.json', 'r') as f:
    print(f'文档总数: {len(json.load(f))}')
"
```

### 3. 测试查询

```bash
# 启动服务
docker-compose up -d

# 测试 LightRAG 查询
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

## 🎯 完整流程示例

### 开发环境（快速测试）

```bash
# 1. 配置（限制 10 条，快速构建）
cat > .env << EOF
OPENAI_API_KEY=sk-your-key
INIT_LIGHTRAG_ON_BUILD=true
LIGHTRAG_INIT_LIMIT=10
EOF

# 2. 构建
bash build-with-lightrag.sh

# 3. 启动
docker-compose up -d

# 4. 测试
curl http://localhost:8000/api/v1/health
```

### 生产环境（完整数据）

```bash
# 1. 配置（完整数据）
cat > .env << EOF
OPENAI_API_KEY=sk-your-key
INIT_LIGHTRAG_ON_BUILD=true
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small
EOF

# 2. 构建
bash build-with-lightrag.sh

# 3. 推送镜像
docker tag gustobot_server:latest registry.example.com/gustobot:v1.0
docker push registry.example.com/gustobot:v1.0

# 4. 在生产服务器拉取并运行
docker pull registry.example.com/gustobot:v1.0
docker-compose up -d
```

---

## 🐛 故障排查

### 问题 1: 构建失败 - API Key 错误

**错误**:
```
❌ ERROR: OPENAI_API_KEY is not set!
```

**解决**:
```bash
# 确保 .env 文件存在并包含正确的 key
echo "OPENAI_API_KEY=sk-your-key" > .env

# 或者直接传递
export OPENAI_API_KEY=sk-your-key
bash build-with-lightrag.sh
```

### 问题 2: 构建超时

**原因**: 处理大量数据耗时长

**解决**:
```bash
# 先用限制数量测试
LIGHTRAG_INIT_LIMIT=10 bash build-with-lightrag.sh

# 确认可行后再完整构建
LIGHTRAG_INIT_LIMIT= bash build-with-lightrag.sh
```

### 问题 3: 镜像太大

**原因**: LightRAG 数据约 50MB

**解决**:
- 这是正常的，数据已包含在镜像中
- 如果需要更小镜像，使用启动时初始化方案

### 问题 4: 文件未生成

**检查**:
```bash
# 查看构建日志
docker-compose build server 2>&1 | grep -A 20 "Initializing LightRAG"

# 确认 build arg 传递正确
docker-compose build --progress=plain server 2>&1 | grep INIT_LIGHTRAG
```

---

## 📊 性能对比

### 构建时间对比

| 场景 | 不初始化 | 初始化 10 条 | 完整初始化 |
|------|---------|-------------|-----------|
| **构建时间** | ~2 分钟 | ~3 分钟 | ~15 分钟 |
| **镜像大小** | ~500MB | ~520MB | ~550MB |
| **启动时间** | < 1 秒 | < 1 秒 | < 1 秒 |

### 启动时间对比

| 方式 | 首次启动 | 后续启动 |
|------|---------|---------|
| **Build 时初始化** | < 1 秒 | < 1 秒 |
| **启动时初始化** | ~5-10 分钟 | < 1 秒 |

---

## 💡 最佳实践

### 1. CI/CD 构建

```yaml
# .github/workflows/build.yml
name: Build Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build with LightRAG
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          docker-compose build \
            --build-arg INIT_LIGHTRAG_ON_BUILD=true \
            --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
            server

      - name: Push to registry
        run: docker push registry.example.com/gustobot:latest
```

### 2. 多阶段构建优化

如果需要更小的最终镜像：

```dockerfile
# 构建阶段：初始化 LightRAG
FROM python:3.11-slim AS builder
# ... 初始化 LightRAG，生成 /app/data/lightrag/

# 运行阶段：只复制必要文件
FROM python:3.11-slim
COPY --from=builder /app /app
# ... 其他配置
```

### 3. 缓存优化

```bash
# 使用 BuildKit 缓存
DOCKER_BUILDKIT=1 docker-compose build \
  --build-arg INIT_LIGHTRAG_ON_BUILD=true \
  --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
  server
```

---

## 🎉 总结

**构建时初始化的优势**:
- ✅ 启动即用，无需等待
- ✅ 数据一致性，一次构建到处运行
- ✅ 适合生产环境和 CI/CD

**使用建议**:
- 💻 **开发**: 先用 `--limit 10` 快速测试
- 🚀 **生产**: 完整构建并推送到镜像仓库
- 🔄 **更新**: 数据更新时重新构建镜像

**快速开始**:
```bash
echo "OPENAI_API_KEY=sk-xxx" > .env && bash build-with-lightrag.sh
```

现在你的 Docker 镜像包含预初始化的 LightRAG 数据了！🎊

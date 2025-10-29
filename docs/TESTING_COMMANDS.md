# GustoBot 测试命令速查表

## 🚀 快速启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f server
```

---

## ✅ 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# 根端点
curl http://localhost:8000/

# 查看 API 文档
open http://localhost:8000/docs  # 或访问 http://localhost:8000/docs
```

---

## 🔧 配置验证

```bash
# 验证所有配置
docker-compose exec server python3 -c "
from gustobot.config.settings import settings
print('LLM:', settings.LLM_MODEL, '@', settings.LLM_BASE_URL)
print('Embedding:', settings.EMBEDDING_MODEL, '@', settings.EMBEDDING_BASE_URL)
print('Reranker:', settings.RERANK_MODEL, '@', settings.RERANK_BASE_URL)
print('Milvus:', settings.MILVUS_HOST + ':' + str(settings.MILVUS_PORT))
print('Redis:', settings.REDIS_HOST + ':' + str(settings.REDIS_PORT))
"

# 简化版本
docker-compose exec server python3 -c "from gustobot.config import settings; print(f'Embedding: {settings.EMBEDDING_MODEL} @ {settings.EMBEDDING_BASE_URL}')"
```

---

## 📊 Neo4j 知识图谱测试

```bash
# 获取图谱数据
curl -s http://localhost:8000/api/v1/knowledge/graph | jq '.nodes[:5]'

# 知识图谱问答
curl -X POST "http://localhost:8000/api/v1/knowledge/graph/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "香肠炒菜干需要什么食材？"
  }' | jq

# 直接访问 Neo4j Browser
open http://localhost:17474
```

---

## 🔍 知识库测试

```bash
# 添加单个菜谱
curl -X POST "http://localhost:8000/api/v1/knowledge/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "红烧肉",
    "category": "家常菜",
    "difficulty": "中等",
    "time": "60分钟",
    "ingredients": ["五花肉500g", "冰糖30g", "生抽3勺"],
    "steps": ["切块", "焯水", "炒糖色", "炖煮"],
    "tips": "糖色不要炒过头"
  }' | jq

# 搜索知识库
curl -X POST "http://localhost:8000/api/v1/knowledge/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "红烧肉怎么做？",
    "top_k": 6
  }' | jq

# 获取知识库统计
curl -s http://localhost:8000/api/v1/knowledge/stats | jq

# 清空知识库（谨慎使用）
curl -X POST "http://localhost:8000/api/v1/knowledge/clear"
```

---

## 🌐 LightRAG 测试

```bash
# 查看 LightRAG 状态
curl -s http://localhost:8000/api/v1/lightrag/stats | jq

# 插入数据到 LightRAG
curl -X POST "http://localhost:8000/api/v1/lightrag/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "红烧肉是一道经典的中式菜肴，主要食材是五花肉、冰糖、生抽等。",
    "description": "红烧肉菜谱"
  }' | jq

# LightRAG 查询
curl -X POST "http://localhost:8000/api/v1/lightrag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "红烧肉怎么做？",
    "mode": "hybrid"
  }' | jq

# 测试不同检索模式
curl -X GET "http://localhost:8000/api/v1/lightrag/test-modes?query=红烧肉" | jq
```

---

## 💬 会话管理测试

```bash
# 创建会话
curl -X POST "http://localhost:8000/api/v1/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "title": "测试对话"
  }' | jq

# 获取用户所有会话
curl -s "http://localhost:8000/api/v1/sessions/?user_id=test_user_001" | jq

# 获取会话消息
curl -s "http://localhost:8000/api/v1/sessions/{session_id}/messages" | jq

# 删除会话
curl -X DELETE "http://localhost:8000/api/v1/sessions/{session_id}"
```

---

## 🔄 Docker 管理命令

```bash
# 重启单个服务
docker-compose restart server

# 重新构建并启动服务
docker-compose up -d --build server

# 查看服务日志（最后 100 行）
docker-compose logs --tail=100 server

# 查看实时日志
docker-compose logs -f server

# 进入容器
docker-compose exec server bash

# 停止所有服务
docker-compose down

# 停止并删除卷（清空所有数据）
docker-compose down -v
```

---

## 🐛 调试命令

```bash
# 检查容器内配置
docker-compose exec server python3 -c "from gustobot.config import settings; print(settings.model_dump_json(indent=2))"

# 测试 Milvus 连接
docker-compose exec server python3 -c "
from pymilvus import connections
connections.connect('default', host='milvus', port='19530')
print('Milvus 连接成功!')
"

# 测试 Redis 连接
docker-compose exec server python3 -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
r.ping()
print('Redis 连接成功!')
"

# 测试 Neo4j 连接
docker-compose exec neo4j cypher-shell -u neo4j -p recipepass "MATCH (n) RETURN count(n) as total"

# 查看 Python 包版本
docker-compose exec server pip list | grep -E "langchain|openai|pymilvus|redis"
```

---

## 📊 性能测试

```bash
# 批量添加菜谱性能测试
time for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/knowledge/recipes" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"测试菜谱$i\", \"category\": \"测试\"}" \
    -s > /dev/null
done

# 并发检索测试（需要安装 ab 工具）
ab -n 100 -c 10 \
  -p test_query.json \
  -T "application/json" \
  http://localhost:8000/api/v1/knowledge/search

# test_query.json 内容：
# {"query": "红烧肉", "top_k": 6}
```

---

## 🔍 日志查询

```bash
# 查找错误日志
docker-compose logs server | grep -i error

# 查找 Milvus 相关日志
docker-compose logs server | grep -i milvus

# 查找 Embedding 调用日志
docker-compose logs server | grep -i embedding

# 查找 Reranker 调用日志
docker-compose logs server | grep -i rerank

# 查看启动日志
docker-compose logs server | grep -E "Starting|Started|INFO"
```

---

## 🧪 集成测试脚本

```bash
# 创建测试脚本 test_integration.sh
cat > test_integration.sh << 'EOF'
#!/bin/bash
set -e

echo "=== GustoBot 集成测试 ==="

echo "1. 检查服务健康..."
curl -f http://localhost:8000/health || exit 1

echo "2. 验证配置..."
docker-compose exec -T server python3 -c "from gustobot.config import settings; assert settings.EMBEDDING_MODEL, 'Embedding model not set'"

echo "3. 测试 Neo4j 图谱..."
curl -f -X POST "http://localhost:8000/api/v1/knowledge/graph/qa" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试"}' > /dev/null || exit 1

echo "4. 测试 LightRAG 状态..."
curl -f http://localhost:8000/api/v1/lightrag/stats > /dev/null || exit 1

echo "✅ 所有测试通过！"
EOF

chmod +x test_integration.sh
./test_integration.sh
```

---

## 📝 常用组合命令

```bash
# 完全重启（清空数据）
docker-compose down -v && docker-compose up -d --build

# 快速重启（保留数据）
docker-compose restart server

# 查看所有服务状态和端口
docker-compose ps

# 导出配置
docker-compose exec server python3 -c "from gustobot.config import settings; import json; print(json.dumps(settings.model_dump(), indent=2, default=str))" > config_export.json

# 备份数据
docker-compose exec neo4j neo4j-admin database dump neo4j --to=/data/backup.dump
docker cp gustobot_neo4j_1:/data/backup.dump ./neo4j_backup.dump
```

---

## 🎯 故障排查

```bash
# 1. 服务无法启动
docker-compose logs --tail=100 server
docker-compose exec server python3 -m gustobot.main  # 直接运行查看错误

# 2. Milvus 连接失败
docker-compose exec server ping -c 3 milvus
docker-compose logs milvus

# 3. Redis 连接失败
docker-compose exec server ping -c 3 redis
docker-compose logs redis

# 4. 配置未生效
docker-compose exec server cat /app/.env
docker-compose restart server

# 5. 端口被占用
netstat -tuln | grep -E '8000|19530|6379|17474'
lsof -i :8000  # macOS/Linux
```

---

## 📚 文档链接

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Neo4j Browser**: http://localhost:17474
- **MinIO Console**: http://localhost:9001

---

**快速参考**:
- 主服务: `http://localhost:8000`
- 健康检查: `curl http://localhost:8000/health`
- 查看日志: `docker-compose logs -f server`
- 重启服务: `docker-compose restart server`

**最后更新**: 2025-10-28

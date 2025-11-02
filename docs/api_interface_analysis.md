# GustoBot API 接口分析报告

## API 接口完整列表

### 1. Knowledge Router (知识库相关)
- `POST /api/v1/knowledge/recipes` - 添加单个菜谱
- `POST /api/v1/knowledge/recipes/batch` - 批量添加菜谱
- `POST /api/v1/knowledge/search` - 搜索知识库
- `DELETE /api/v1/knowledge/recipes/{recipe_id}` - 删除菜谱
- `GET /api/v1/knowledge/stats` - 获取知识库统计
- `DELETE /api/v1/knowledge/clear` - 清空知识库
- `GET /api/v1/knowledge/graph` - 获取知识图谱信息
- `POST /api/v1/knowledge/graph/qa` - 知识图谱问答

### 2. LightRAG Router (图推理相关)
- `POST /api/v1/lightrag/query` - LightRAG查询
- `POST /api/v1/lightrag/query-stream` - LightRAG流式查询
- `POST /api/v1/lightrag/insert` - 插入数据到LightRAG
- `GET /api/v1/lightrag/stats` - LightRAG统计信息
- `POST /api/v1/lightrag/test-modes` - 测试LightRAG模式

### 3. Chat Router (聊天相关) ⚠️
- `POST /api/v1/chat/chat` - 统一聊天接口（主要接口）
- `POST /api/v1/chat/chat/stream` - 流式聊天
- `GET /api/v1/chat/chat/history/{session_id}` - 获取聊天历史
- `DELETE /api/v1/chat/chat/session/{session_id}` - 删除会话
- `GET /api/v1/chat/chat/routes` - 获取路由信息

### 4. Sessions Router (会话管理)
- `GET /api/v1/sessions/` - 获取会话列表
- `POST /api/v1/sessions/` - 创建新会话
- `GET /api/v1/sessions/{session_id}` - 获取会话详情
- `PATCH /api/v1/sessions/{session_id}` - 更新会话
- `DELETE /api/v1/sessions/{session_id}` - 删除会话
- `POST /api/v1/sessions/{session_id}/messages` - 添加消息
- `POST /api/v1/sessions/{session_id}/snapshot` - 创建快照
- `GET /api/v1/sessions/user/{user_id}/count` - 获取用户会话数

### 5. Upload Router (文件上传)
- `POST /api/v1/upload/upload/file` - 上传文件
- `POST /api/v1/upload/upload/image` - 上传图片
- `GET /api/v1/upload/uploads/{filename}` - 获取上传的文件
- `DELETE /api/v1/upload/upload/{file_id}` - 删除上传的文件

### 6. System APIs (系统相关)
- `GET /api` - API基本信息
- `GET /health` - 健康检查

## 关于 `/api/v1/chat/chat` 的双重路径问题

这是一个设计问题：
1. 在 `main.py` 中，`api_v1_router` 被挂载到 `/api/v1` 前缀下
2. 在 `v1/__init__.py` 中，`chat.router` 被挂载到 `/chat` 前缀下
3. 在 `chat.py` 中，路由定义为 `@router.post("/chat")`
4. 最终路径变成了：`/api/v1` + `/chat` + `/chat` = `/api/v1/chat/chat`

**建议修复方案**：
- 方案1：在 `chat.py` 中将路由改为 `@router.post("/")`，这样最终路径是 `/api/v1/chat`
- 方案2：在 `v1/__init__.py` 中改为 `api_router.include_router(chat.router, tags=["Unified Chat"])`，去掉前缀

## PostgreSQL 在 kb-query 中的作用

### 当前配置问题
1. **环境变量错误**：
   - 当前值：`INGEST_SERVICE_URL=http://localhost:8000`
   - 应该是：`INGEST_SERVICE_URL=http://kb_ingest:8000`
   - 这导致backend容器无法连接到kb_ingest服务

2. **PostgreSQL/kb_ingest 服务状态**：
   - ✅ kb_postgres 容器正常运行（端口5433）
   - ✅ kb_ingest 容器正常运行（端口8100）
   - ❌ backend无法连接到kb_ingest

### kb-query 路由的工作流程
当用户发送kb-query类型的请求时：
1. Agent路由识别为知识库查询
2. 调用 `create_kb_query` 节点
3. 该节点会尝试：
   - 优先查询PostgreSQL（通过kb_ingest服务）
   - 如果PostgreSQL无结果，fallback到Milvus向量库
   - 返回搜索结果

### 验证PostgreSQL是否生效
从之前的测试日志可以看到：
```
Cannot connect to host localhost:8000 when the workflow tried the Postgres knowledge service
after which it fell back to Milvus with zero hits
```

这表明：
- 系统确实想使用PostgreSQL（kb_ingest服务）
- 但因为连接失败，fallback到了Milvus
- Milvus返回了0个结果

### 修复步骤
1. 在 `docker-compose.yml` 的 backend 服务中添加：
   ```yaml
   environment:
     - INGEST_SERVICE_URL=http://kb_ingest:8000
   ```

2. 或在 `.env` 文件中设置：
   ```
   INGEST_SERVICE_URL=http://kb_ingest:8000
   ```

3. 重启backend服务：
   ```bash
   docker-compose restart backend
   ```

### 预期效果
修复后，kb-query查询应该：
1. 成功连接到kb_ingest服务
2. 优先从PostgreSQL检索结构化数据
3. 返回相关的知识库内容

## 总结

1. **API路径问题**：`/api/v1/chat/chat` 是配置问题，建议修改路由定义
2. **PostgreSQL问题**：环境变量配置错误，需要使用Docker服务名
3. **kb-query现状**：目前因为无法连接PostgreSQL，实际只使用了Milvus，但Milvus中可能没有数据，所以返回空结果

建议优先修复INGEST_SERVICE_URL配置，这样kb-query路由才能正常工作。
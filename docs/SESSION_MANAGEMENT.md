# Lightweight Session Management

GustoBot 轻量级会话管理系统 - 基于 user_id 的会话分组，无需用户认证。

## 📋 功能特性

- ✅ **轻量级用户识别** - 通过 user_id 分组会话，无需注册/登录
- ✅ **灵活的用户ID** - 支持设备ID、UUID或匿名（null）
- ✅ **持久化存储** - SQLite/MySQL 数据库存储
- ✅ **会话管理** - 创建、查询、更新、删除会话
- ✅ **按用户过滤** - 根据 user_id 查询该用户的所有会话
- ✅ **消息存储** - 结构化存储对话消息
- ✅ **快照功能** - 快速恢复完整对话上下文
- ✅ **软删除** - 标记删除，可恢复

## 🏗️ 架构

```
会话管理系统:
├── Models (gustobot/models/)
│   ├── chat_session.py          # 会话模型
│   └── chat_message.py          # 消息+快照模型
│
├── CRUD (gustobot/crud/)
│   ├── crud_chat_session.py     # 会话操作
│   └── crud_chat_message.py     # 消息操作
│
└── API (gustobot/api/v1/sessions.py)
    ├── GET  /api/v1/sessions/                 # 获取会话列表（可选 user_id 过滤）
    ├── POST /api/v1/sessions/                 # 创建会话
    ├── GET  /api/v1/sessions/{id}             # 获取单个会话
    ├── PATCH /api/v1/sessions/{id}            # 更新会话
    ├── DELETE /api/v1/sessions/{id}           # 删除会话
    ├── POST /api/v1/sessions/{id}/messages    # 添加消息
    ├── POST /api/v1/sessions/{id}/snapshot    # 创建快照
    └── GET  /api/v1/sessions/user/{user_id}/count  # 获取用户会话数量
```

## 💡 轻量级 user_id 设计

### 核心概念
- **无需认证**: 不需要用户注册、登录、密码
- **前端提供**: user_id 由前端生成和管理（设备ID、UUID等）
- **灵活可选**: user_id 可为 null（完全匿名会话）
- **会话分组**: 按 user_id 查询该用户的所有会话

### user_id 来源示例
```javascript
// 前端生成 user_id 示例
// 方案1: 设备指纹
const user_id = navigator.userAgent + navigator.hardwareConcurrency;

// 方案2: localStorage UUID
let user_id = localStorage.getItem('user_id');
if (!user_id) {
  user_id = crypto.randomUUID();
  localStorage.setItem('user_id', user_id);
}

// 方案3: 完全匿名（不提供 user_id）
const user_id = null;
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务（自动创建表）

```bash
python -m uvicorn gustobot.main:application --reload
```

**服务启动时会自动创建以下表：**
- `chat_sessions` - 会话表
- `chat_messages` - 消息表
- `chat_history_snapshots` - 快照表

### 3. 访问 API 文档

http://localhost:8000/docs

## 📚 API 使用示例

### 1. 创建会话（带 user_id）

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "红烧肉怎么做",
    "user_id": "device-12345-abcde"
  }'
```

**响应:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "红烧肉怎么做",
  "user_id": "device-12345-abcde",
  "created_at": "2025-10-27T19:30:00",
  "updated_at": null,
  "is_active": true
}
```

### 2. 创建匿名会话（不提供 user_id）

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "匿名会话"
  }'
```

### 3. 获取所有会话

```bash
curl -X GET "http://localhost:8000/api/v1/sessions/?skip=0&limit=20"
```

### 4. 获取特定用户的会话

```bash
# 只获取 user_id 为 "device-12345-abcde" 的会话
curl -X GET "http://localhost:8000/api/v1/sessions/?user_id=device-12345-abcde&skip=0&limit=20"
```

### 5. 获取单个会话

```bash
curl -X GET "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000"
```

### 6. 获取用户会话数量

```bash
curl -X GET "http://localhost:8000/api/v1/sessions/user/device-12345-abcde/count"
```

**响应:**
```json
{
  "user_id": "device-12345-abcde",
  "session_count": 5
}
```

### 7. 添加消息到会话

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "user_query",
    "content": "怎么做红烧肉？",
    "order_index": 1
  }'
```

### 8. 创建对话快照

```bash
curl -X POST "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/snapshot" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "query": "怎么做红烧肉？",
    "response_data": {
      "answer": "红烧肉的做法...",
      "route": "knowledge",
      "confidence": 0.95,
      "sources": ["recipe_001", "recipe_045"]
    }
  }'
```

### 9. 更新会话

```bash
# 可以更新 title, user_id, is_active
curl -X PATCH "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "红烧肉的完整教程",
    "user_id": "device-new-user-id"
  }'
```

### 10. 删除会话（软删除）

```bash
curl -X DELETE "http://localhost:8000/api/v1/sessions/550e8400-e29b-41d4-a716-446655440000"
```

## 🗄️ 数据库表结构

### chat_sessions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(255) | Session UUID (主键) |
| user_id | String(255) | 用户标识符（设备ID、UUID等），nullable |
| title | String(500) | 会话标题 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| is_active | Boolean | 是否活跃（软删除标记） |

**重要说明:**
- `user_id` 字段为 String 类型，**无外键约束**
- `user_id` 可为 null（支持完全匿名会话）
- 通过 `user_id` 索引支持快速按用户查询
- 无需 User 表或认证系统

### chat_messages 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 自增主键 |
| session_id | String(255) | 所属会话ID (外键) |
| message_type | String(50) | 消息类型 |
| content | Text | 消息内容 |
| message_metadata | JSON | 元数据 |
| order_index | Integer | 消息顺序 |
| created_at | DateTime | 创建时间 |

**message_type 取值:**
- `user_query` - 用户查询
- `agent_response` - Agent 回复
- `knowledge` - 知识库回复
- `error` - 错误消息

### chat_history_snapshots 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 自增主键 |
| session_id | String(255) | 所属会话ID (外键) |
| query | Text | 原始用户查询 |
| response_data | JSON | 完整响应数据 |
| created_at | DateTime | 创建时间 |

## 💡 集成到现有 Agent 系统

### 在 Chat API 中保存会话

```python
from uuid import uuid4
from gustobot.infrastructure.persistence.crud import chat_session, chat_message, chat_session_snapshot
from gustobot.interfaces.http.models.chat_session import ChatSessionCreate
from gustobot.interfaces.http.models.chat_message import ChatMessageCreate, ChatSessionSnapshotCreate

@router.post("/chat")
async def chat(
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,  # 前端提供的 user_id
    db: Session = Depends(get_db)
):
    # 创建或获取会话
    if not session_id:
        session_id = str(uuid4())
        chat_session.create(db, obj_in=ChatSessionCreate(
            id=session_id,
            title=message[:100],  # 使用第一条消息作为标题
            user_id=user_id  # 可选的用户标识符
        ))

    # 保存用户消息
    chat_message.create(db, obj_in=ChatMessageCreate(
        session_id=session_id,
        message_type="user_query",
        content=message,
        order_index=1
    ))

    # 调用 Agent 系统处理
    response = await agent_system.process(message)

    # 保存 Agent 响应
    chat_message.create(db, obj_in=ChatMessageCreate(
        session_id=session_id,
        message_type="agent_response",
        content=response["answer"],
        message_metadata=response.get("metadata"),
        order_index=2
    ))

    # 创建快照以便快速恢复
    chat_session_snapshot.create(db, obj_in=ChatSessionSnapshotCreate(
        session_id=session_id,
        query=message,
        response_data=response
    ))

    # 更新会话活动时间
    chat_session.update_activity(db, session_id=session_id)

    return {
        "session_id": session_id,
        "user_id": user_id,
        **response
    }
```

## 🔄 双存储策略

推荐使用 **Redis + 数据库** 双存储：

- **Redis** - 临时快速缓存（TTL 3天）
- **Database** - 永久持久化存储

### 优势：
- Redis 提供快速响应
- Database 提供长期存储
- 互为备份，提高可靠性

## 🧪 测试

在 Swagger UI 测试所有端点：http://localhost:8000/docs

### 测试流程：
1. ✅ 创建新会话
2. ✅ 添加消息到会话
3. ✅ 创建对话快照
4. ✅ 获取会话列表
5. ✅ 获取单个会话详情
6. ✅ 更新会话标题
7. ✅ 删除会话

## 📊 与 ChatDB 对比

| 特性 | ChatDB | GustoBot |
|------|--------|----------|
| **用户认证** | ✅ JWT + 密码 | ❌ 无认证 |
| **用户识别** | ✅ User表 + FK | ✅ 轻量级 user_id (String) |
| **会话分组** | ✅ 按用户 | ✅ 按 user_id |
| **会话管理** | ✅ 持久化 | ✅ 持久化 |
| **消息存储** | ✅ 结构化 | ✅ 结构化 |
| **快照功能** | ✅ 有 | ✅ 有 |
| **使用场景** | 企业 Text2SQL | 智能菜谱助手 |

## 🎯 下一步

1. **集成到现有 Chat API** - 在 `/api/v1/chat` 中添加会话持久化
2. **添加会话搜索** - 根据标题或内容搜索会话
3. **添加会话导出** - 导出对话历史为 JSON/Markdown
4. **添加会话统计** - 统计会话数量、消息数量等
5. **添加清理任务** - 定期清理过期的非活跃会话

## 🐛 故障排查

### 问题: "Table doesn't exist"
**解决:** 重启服务，表会自动创建
```bash
python -m uvicorn gustobot.main:application --reload
```

### 问题: "Foreign key constraint failed"
**解决:** 确保先创建会话，再添加消息

### 问题: 导入错误
**解决:** 确保所有依赖已安装
```bash
pip install -r requirements.txt
```

### 问题: 需要重建数据库
**解决:** 删除数据库文件并重启
```bash
rm ./data/gustobot.db
python -m uvicorn gustobot.main:application --reload
```

## 📖 相关文档

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)

---

**轻量级会话管理系统，支持 user_id 分组但无需认证！** 🎉

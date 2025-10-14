# LangGraph 架构迁移指南

## 概述

本文档记录了 GustoBot 从旧版 LangGraph 架构迁移到现代化纯函数节点架构的过程。

## 主要改进

### 1. **升级 LangGraph 版本**
- **旧版本**: `langgraph==0.0.25`
- **新版本**: `langgraph==0.2.60` + `langgraph-checkpoint==2.0.8`

### 2. **状态管理优化**
**之前**: 使用 Pydantic `BaseModel`
```python
class ConversationState(BaseModel):
    message: str
    session_id: Optional[str] = None
    # ...

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
```

**现在**: 使用 `TypedDict` (推荐的 LangGraph 模式)
```python
class ConversationState(TypedDict):
    message: str  # Required
    session_id: NotRequired[Optional[str]]
    # ...
```

**优点**:
- 更好的类型检查和 IDE 支持
- 与 LangGraph 原生集成更好
- 更轻量级，无需序列化/反序列化开销

### 3. **Agent 架构重构**

#### 之前: 类式 Agent
每个 Agent 是一个独立的类：
```python
class RouterAgent(BaseAgent):
    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__(name="RouterAgent", description="...")
        self.llm_client = llm_client

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # 路由逻辑...
        pass
```

#### 现在: 纯函数节点
所有 Agent 逻辑提取为纯函数：
```python
async def route_question(
    state: ConversationState,
    llm_client: Optional[LLMClient] = None,
) -> ConversationState:
    """Pure function that takes state and returns updated state."""
    # 路由逻辑...
    return {**state, "route": decision["route"], ...}
```

**优点**:
- 更容易测试（纯函数，无副作用）
- 更容易组合和复用
- 依赖注入更清晰
- 符合 LangGraph 最佳实践

### 4. **流式输出支持**

新架构原生支持流式输出：

```python
# 在 SupervisorAgent
async def stream(self, input_data: Dict[str, Any]):
    """Stream workflow execution events."""
    async for event in self.workflow.astream(initial_state):
        yield event

# 在 API
@router.post("/stream")
async def chat_stream(request: ChatRequest, supervisor = Depends(get_supervisor)):
    async def event_generator() -> AsyncIterator[str]:
        async for event in supervisor.stream(input_data):
            yield f"data: {json.dumps(event_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

## 文件结构变化

### 新增文件
```
app/agents/
├── nodes.py                      # 新增: 所有纯函数节点
├── supervisor_agent_v2.py        # 新增: 重构后的 SupervisorAgent
└── state_models.py               # 修改: 使用 TypedDict
```

### 保留文件（向后兼容）
```
app/agents/
├── base_agent.py                 # 保留: 如果需要类式 Agent
├── router_agent.py               # 保留: 旧版类式实现
├── knowledge_agent.py            # 保留: 旧版类式实现
├── chat_agent.py                 # 保留: 旧版类式实现
└── supervisor_agent.py           # 保留: 旧版实现
```

## 工作流图结构

### 节点定义变化

**之前**:
```python
# SupervisorAgent._build_graph()
async def route_node(state: dict) -> dict:
    conv = ConversationState.model_validate(state)
    route_result = await self.router.process({...})
    # ...
```

**现在**:
```python
# supervisor_agent_v2.py
from functools import partial

# 使用 partial 绑定依赖
graph.add_node(
    "route",
    partial(route_question, llm_client=self.llm_client)
)
```

### 完整工作流

```
START
  ↓
prepare_context  (加载历史, 准备缓存上下文)
  ↓
check_cache     (检查语义缓存)
  ↓
[条件分支: cached? → finalize : route]
  ↓
route           (路由分类: knowledge/chat/reject)
  ↓
[条件分支: knowledge → knowledge_node]
           [chat → chat_node]
           [reject → finalize]
  ↓
finalize        (持久化历史, 更新缓存)
  ↓
END
```

## 迁移步骤

### Step 1: 更新依赖
```bash
pip install -r requirements.txt
```

### Step 2: 更新 API 端点导入

**旧代码** (`app/api/chat_router.py`):
```python
def get_supervisor():
    from ..agents import SupervisorAgent, RouterAgent, KnowledgeAgent, ChatAgent

    router_agent = RouterAgent()
    knowledge_agent = KnowledgeAgent(knowledge_service=knowledge_service)
    chat_agent = ChatAgent()

    supervisor = SupervisorAgent(
        router=router_agent,
        knowledge=knowledge_agent,
        chat=chat_agent,
        ...
    )
```

**新代码**:
```python
def get_supervisor():
    from ..agents.supervisor_agent_v2 import SupervisorAgent
    from ..knowledge_base import KnowledgeService

    knowledge_service = KnowledgeService()
    llm_client = LLMClient()

    supervisor = SupervisorAgent(
        knowledge_service=knowledge_service,
        llm_client=llm_client,
        semantic_cache=_semantic_cache,
        history_store=_history_store,
    )
```

### Step 3: 使用新 API

#### 标准调用（非流式）
```python
# POST /api/v1/chat/
result = await supervisor.process({
    "message": "如何做红烧肉？",
    "session_id": "xxx",
    "user_id": "user123"
})
# 返回: {"answer": "...", "type": "knowledge", "metadata": {...}}
```

#### 流式调用
```python
# POST /api/v1/chat/stream
async for event in supervisor.stream(input_data):
    # 每个节点执行后会产生事件
    print(event)
```

## API 端点变化

| 端点 | 方法 | 状态 | 说明 |
|-----|------|-----|------|
| `/api/v1/chat/` | POST | ✅ 兼容 | 标准聊天接口，使用新 SupervisorAgent |
| `/api/v1/chat/stream` | POST | 🆕 新增 | 流式聊天接口 (SSE) |
| `/api/v1/chat/status` | GET | ✅ 更新 | 返回新版本信息 |

## 测试建议

### 1. 单元测试节点函数
```python
# tests/test_nodes.py
import pytest
from app.agents.nodes import route_question
from app.agents.state_models import ConversationState

@pytest.mark.asyncio
async def test_route_question():
    state: ConversationState = {"message": "如何做红烧肉？"}
    result = await route_question(state, llm_client=None)

    assert result["route"] == "knowledge"
    assert result["confidence"] > 0.5
```

### 2. 集成测试工作流
```python
# tests/test_supervisor_v2.py
@pytest.mark.asyncio
async def test_supervisor_workflow():
    supervisor = SupervisorAgent(
        knowledge_service=mock_knowledge_service,
        llm_client=mock_llm_client
    )

    result = await supervisor.process({
        "message": "你好",
        "session_id": "test_session"
    })

    assert result["answer"]
    assert result["type"] in ["knowledge", "chat", "reject"]
```

### 3. 流式输出测试
```python
@pytest.mark.asyncio
async def test_streaming():
    events = []
    async for event in supervisor.stream(input_data):
        events.append(event)

    assert len(events) > 0
    # 验证最终状态包含答案
```

## 性能对比

| 指标 | 旧架构 | 新架构 | 改进 |
|-----|-------|-------|-----|
| 类型安全 | Pydantic 运行时验证 | TypedDict 编译时检查 | ✅ 更快 |
| 内存占用 | 每次创建 Pydantic 对象 | 直接操作 dict | ✅ 更低 |
| 测试复杂度 | 需要 mock 多个 Agent 类 | 测试纯函数即可 | ✅ 更简单 |
| 流式支持 | 不支持 | 原生支持 | 🆕 新功能 |

## 常见问题

### Q1: 旧代码还能用吗？
**A**: 可以。旧的 Agent 类（`router_agent.py`, `knowledge_agent.py`, `chat_agent.py`）仍然保留，但推荐迁移到新架构。

### Q2: 如何逐步迁移？
**A**:
1. 先在开发环境测试新 API `/api/v1/chat/` （已自动使用新 SupervisorAgent）
2. 确认功能正常后，逐步切换生产流量
3. 旧 Agent 类可以保留一段时间作为备用

### Q3: 流式输出如何在前端使用？
**A**:
```javascript
// 使用 EventSource 或 fetch
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: '如何做红烧肉？'})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log('Event:', data);
    }
  }
}
```

### Q4: TypedDict 和 Pydantic 有什么区别？
**A**:
- **TypedDict**: 静态类型提示，编译时检查，零运行时开销
- **Pydantic**: 运行时验证，提供数据转换和验证功能
- **选择**: LangGraph 推荐 TypedDict 用于状态，Pydantic 用于 API 输入输出

## 下一步优化建议

1. **添加持久化检查点**
   ```python
   from langgraph.checkpoint import MemorySaver

   checkpointer = MemorySaver()
   workflow = graph.compile(checkpointer=checkpointer)
   ```

2. **可视化工作流**
   ```python
   from IPython.display import Image

   Image(supervisor.workflow.get_graph().draw_mermaid_png())
   ```

3. **添加 Human-in-the-loop**
   ```python
   graph.add_node("human_approval", human_approval_node)
   graph.add_edge("knowledge", "human_approval")
   ```

4. **监控和追踪**
   ```python
   from langsmith import Client

   # 使用 LangSmith 追踪工作流执行
   ```

## 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [TypedDict 文档](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- [FastAPI Streaming](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

## 总结

新架构的主要优势：
- ✅ **更好的类型安全**: TypedDict 提供编译时检查
- ✅ **更易测试**: 纯函数节点，无副作用
- ✅ **更高性能**: 减少对象创建和序列化开销
- ✅ **流式支持**: 原生支持实时响应
- ✅ **更符合最佳实践**: 遵循 LangGraph 推荐模式

建议尽快完成迁移以享受这些改进！

# LightRAG Node 修复总结

## 🎯 修复的问题

### 1. ❌ 错误的 LightRAG 初始化方式

**问题**：使用了不存在的 `llm_model_name` 和 `embedding_model_name` 参数

```python
# ❌ 错误的方式
self.rag = LightRAG(
    working_dir=self.working_dir,
    llm_model_name=settings.OPENAI_MODEL,  # 不存在的参数
    llm_model_kwargs={...},
    embedding_model_name=settings.EMBEDDING_MODEL,  # 不存在的参数
    embedding_model_kwargs={...},
)
```

**修复**：使用 `llm_model_func` 和 `embedding_func`

```python
# ✅ 正确的方式
self.rag = LightRAG(
    working_dir=self.working_dir,
    llm_model_func=self._llm_model_func,  # 函数引用
    embedding_func=EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=self.max_token_size,
        func=self._embedding_func,
    ),
)
```

---

### 2. ❌ 错误的 Neo4JStorage 初始化

**问题**：尝试直接实例化 `Neo4JStorage` 并传递构造参数

```python
# ❌ 错误的方式
from lightrag.kg.neo4j_impl import Neo4JStorage

graph_storage = Neo4JStorage(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD,
    database=settings.NEO4J_DATABASE
)
```

**修复**：使用字符串名称，LightRAG 会自动加载

```python
# ✅ 正确的方式
# 设置环境变量
os.environ["NEO4J_URI"] = settings.NEO4J_URI
os.environ["NEO4J_USERNAME"] = settings.NEO4J_USER
os.environ["NEO4J_PASSWORD"] = settings.NEO4J_PASSWORD
os.environ["NEO4J_DATABASE"] = settings.NEO4J_DATABASE

# 传递字符串名称
graph_storage_type = "Neo4JStorage"  # 类型: str
self.rag = LightRAG(graph_storage=graph_storage_type)
```

---

### 3. ❌ QueryParam 参数错误

**问题**：使用了不存在的 `max_token_for_text_unit` 参数

```python
# ❌ 错误的方式
param = QueryParam(
    mode=retrieval_mode,
    top_k=self.top_k,
    max_token_for_text_unit=self.max_token_size,  # 不存在的参数
)
```

**修复**：只使用 `QueryParam` 支持的参数

```python
# ✅ 正确的方式
param = QueryParam(
    mode=retrieval_mode,
    top_k=self.top_k,
    # 其他参数如 max_entity_tokens、max_relation_tokens 可通过环境变量配置
)
```

---

### 4. ❌ graph_storage 类型错误

**问题**：`graph_storage` 变量类型为 `str | None`，导致类型检查错误

```python
# ❌ 类型错误
graph_storage = "Neo4JStorage" if ... else None  # str | None
```

**修复**：始终使用字符串类型

```python
# ✅ 类型正确
graph_storage_type = "Neo4JStorage" if ... else "NetworkXStorage"  # str
```

---

### 5. ❌ Embedding 函数返回类型错误

**问题**：`openai_embed` 返回 `np.ndarray`，但类型注解声明为 `List[List[float]]`

```python
# ❌ 类型不匹配
async def _embedding_func(self, texts: List[str]) -> List[List[float]]:
    return await openai_embed(...)  # 实际返回 np.ndarray
```

**修复**：修正返回类型注解并添加 numpy 导入

```python
# ✅ 类型正确
import numpy as np

async def _embedding_func(self, texts: List[str]) -> np.ndarray:
    """嵌入向量数组，形状为 (len(texts), embedding_dim)"""
    return await openai_embed(
        texts=texts,
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
    )
```

---

## 📋 完整的正确实现

### LLM 函数

```python
async def _llm_model_func(
    self,
    prompt,
    system_prompt=None,
    history_messages=[],
    keyword_extraction=False,
    **kwargs
) -> str:
    """LLM 模型函数，用于 LightRAG 调用"""
    return await openai_complete_if_cache(
        model=settings.OPENAI_MODEL,
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
        **kwargs,
    )
```

### Embedding 函数

```python
import numpy as np

async def _embedding_func(self, texts: List[str]) -> np.ndarray:
    """
    Embedding 函数，用于 LightRAG 调用

    返回 np.ndarray，形状为 (len(texts), embedding_dim)
    """
    return await openai_embed(
        texts=texts,
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
    )
```

### 初始化 LightRAG

```python
async def initialize(self):
    """初始化 LightRAG 实例"""
    # 配置 Neo4j
    if self.enable_neo4j and settings.NEO4J_URI:
        os.environ["NEO4J_URI"] = settings.NEO4J_URI
        os.environ["NEO4J_USERNAME"] = settings.NEO4J_USER
        os.environ["NEO4J_PASSWORD"] = settings.NEO4J_PASSWORD
        os.environ["NEO4J_DATABASE"] = settings.NEO4J_DATABASE
        graph_storage_type = "Neo4JStorage"
    else:
        graph_storage_type = "NetworkXStorage"

    # 创建 LightRAG 实例
    self.rag = LightRAG(
        working_dir=self.working_dir,
        llm_model_func=self._llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=int(settings.EMBEDDING_DIMENSION),
            max_token_size=self.max_token_size,
            func=self._embedding_func,
        ),
        graph_storage=graph_storage_type,
    )

    # 初始化存储
    await self.rag.initialize_storages()
```

### 查询

```python
async def query(self, query: str, mode: Optional[str] = None) -> Dict[str, Any]:
    """执行 LightRAG 查询"""
    await self.initialize()

    retrieval_mode = mode or self.retrieval_mode

    # 创建查询参数
    param = QueryParam(
        mode=retrieval_mode,
        top_k=self.top_k,
    )

    # 执行查询
    response = await self.rag.aquery(query, param=param)

    return {
        "response": response,
        "mode": retrieval_mode,
        "query": query
    }
```

---

## 🔍 与官方示例对比

### MongoDB 示例（官方）

```python
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,  # ✅ 函数
    embedding_func=embedding_func_instance,  # ✅ EmbeddingFunc
    graph_storage="MongoGraphStorage",  # ✅ 字符串
)
```

### Dickens 示例（官方）

```python
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=llm_model_func,  # ✅ 函数
    embedding_func=EmbeddingFunc(  # ✅ EmbeddingFunc
        embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
        max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
        func=lambda texts: ollama_embed(...),
    ),
    # 没有 graph_storage = 使用默认 NetworkXStorage
)
```

### 本项目（修复后）

```python
self.rag = LightRAG(
    working_dir=self.working_dir,
    llm_model_func=self._llm_model_func,  # ✅ 函数
    embedding_func=EmbeddingFunc(  # ✅ EmbeddingFunc
        embedding_dim=embedding_dim,
        max_token_size=self.max_token_size,
        func=self._embedding_func,
    ),
    graph_storage=graph_storage_type,  # ✅ 字符串
)
```

**✅ 完全一致！**

---

## 📝 QueryParam 支持的参数

根据 LightRAG 源码，`QueryParam` 支持以下参数：

```python
@dataclass
class QueryParam:
    mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = "mix"
    only_need_context: bool = False
    only_need_prompt: bool = False
    response_type: str = "Multiple Paragraphs"
    stream: bool = False
    top_k: int = ...
    chunk_top_k: int = ...
    max_entity_tokens: int = ...
    max_relation_tokens: int = ...
    max_total_tokens: int = ...
    hl_keywords: list[str] = ...
    ll_keywords: list[str] = ...
    conversation_history: list[dict[str, str]] = ...
    history_turns: int = ...
    model_func: Callable | None = None
    user_prompt: str | None = None
    enable_rerank: bool = True
    include_references: bool = False
```

**注意**：没有 `max_token_for_text_unit` 参数！

---

## 🧪 测试验证

运行测试脚本：

```bash
python test_lightrag_node.py
```

### 测试覆盖：

1. ✅ LightRAG 初始化
2. ✅ Embedding 功能
3. ✅ 文档插入
4. ✅ 查询功能（naive、local、global、hybrid）
5. ✅ Neo4j 集成（可选）

---

## 🎉 总结

所有修复已完成，代码现在：

- ✅ 完全符合 LightRAG 官方 API
- ✅ 类型检查通过
- ✅ 支持 Neo4j 和 NetworkX 两种图存储
- ✅ 参数配置清晰、可维护
- ✅ 与官方示例代码风格一致

---

## 📚 参考资料

- **LightRAG GitHub**: https://github.com/HKUDS/LightRAG
- **官方示例**:
  - `examples/lightrag_openai_compatible_demo.py`
  - `examples/mongodb_demo.py`
- **类定义**: `lightrag/__init__.py` 中的 `LightRAG` 和 `QueryParam` 类

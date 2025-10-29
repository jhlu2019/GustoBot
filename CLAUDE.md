# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GustoBot** is an enterprise-grade intelligent recipe assistant system (菜谱智能客服) featuring a Multi-Agent architecture with hybrid knowledge retrieval. The system combines vector-based RAG, knowledge graph reasoning (Neo4j), and GraphRAG for comprehensive recipe recommendations and cooking assistance.

### Key Features

- **Multi-Agent Architecture**: LangGraph-based coordination of routing, knowledge retrieval, and chat agents
- **Hybrid Knowledge Retrieval**:
  - Vector RAG (Milvus + OpenAI Embedding + Reranker)
  - Knowledge Graph (Neo4j) for structured recipe relationships
  - GraphRAG integration for graph-based reasoning
- **Semantic Caching**: Redis-based LLM response caching with Ollama embeddings
- **Smart Routing**: LLM-powered question classification (knowledge/chat/reject)
- **Web Crawler Framework**: HTTP + Browser automation for recipe data collection
- **Full-stack**: FastAPI server + React web frontend

## Development Commands

### Server (Backend)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run server (development mode)
python -m uvicorn gustobot.main:application --reload --host 0.0.0.0 --port 8000
# Or use: make run-server

# Run tests
pytest tests/ -v
# Or use: make test

# Code formatting and linting
black gustobot/
flake8 gustobot/ --max-line-length=100
mypy gustobot/
# Or use: make format and make lint
```

### Web (Frontend)

```bash
# Install Node dependencies
cd web && npm install

# Run web dev server
cd web && npm run dev
# Or use: make run-web

# Build for production
cd web && npm run build
```

### Combined Development

```bash
# Run both server and web concurrently
make dev

# Docker development
docker-compose up -d
```

### Knowledge Base Management

```bash
# Initialize data directories
make init-data

# Add recipes via API (see gustobot/api/knowledge.py for endpoints)
# POST /api/v1/knowledge/recipes
# POST /api/v1/knowledge/recipes/batch
```

## Architecture

### High-Level System Flow

```
User Query → LangGraph Supervisor → Semantic Cache Check
                    ↓ (cache miss)
        ┌───────────── analyze_and_route_query ─────────────┐
        │                       │                          │
    kb-query               general-query                 reject
        ↓                       ↓                          ↓
 KB Multi-Tool           respond_to_general_query     安全拒绝输出
   Workflow
        ↓
[Milvus | PostgreSQL | External]
        ↓
 Cache Response → Return to User
```

### Multi-Agent System (LangGraph-based)

1. **SupervisorAgent** (`gustobot/application/agents/supervisor_agent.py`) - LangGraph workflow coordinator
   - Builds state graph with nodes: prepare_context → check_cache → route → execute → save_history
   - Manages Redis conversation history and semantic caching
   - Implements conditional routing logic

2. **LangGraph Router & Guardrails** (`gustobot/application/agents/lg_builder.py`)
   - `analyze_and_route_query`、`safety_guardrails` 等节点负责分类与合规检查
   - 路由结果覆盖 `kb-query`、`general-query`、`graphrag-query` 等路径
   - 统一写入 LangGraph 检查点以供后续节点复用

3. **KB Multi-Tool Workflow** (`kg_sub_graph/agentic_rag_agents/workflows/multi_agent/multi_tool.py`)
   - 与最新多源检索逻辑一致：Milvus + PostgreSQL（pgvector）+ 可选外部搜索
   - 支持 Guardrails、路由、Milvus/Postgres 查询、外部检索、回答融合
   - 现在会根据路由工具列表动态选择 Milvus/Postgres，并合并来源

4. **General / Research Nodes** (`gustobot/application/agents/lg_builder.py`)
   - `respond_to_general_query`：闲聊与常识问答
   - `create_research_plan`：生成多步查询计划
   - `create_file_query`、`create_image_query` 等辅助节点

5. **State Management** (`gustobot/application/agents/lg_states.py`)
   - Dataclass + TypedDict 描述路由结果、消息历史、步骤追踪
   - 提供 `InputState`/`AgentState` 等结构，保持节点间的类型安全

### Knowledge Systems

The project implements **three complementary knowledge retrieval systems**:

#### 1. Vector RAG (`gustobot/infrastructure/knowledge/`)

- **VectorStore** (`vector_store.py`): Milvus vector database
  - IVF_FLAT indexing with Inner Product (IP) metric
  - Persistent storage via Docker volumes

- **EmbeddingService** (`embedding_service.py`): OpenAI text-embedding-3-small (1536-dim)

- **Reranker** (`reranker.py`): Multi-provider reranking
  - Supports: Cohere, Jina AI, Voyage AI, BGE
  - Two-stage: Milvus recall (top_k × 3) → API rerank (top_k)

- **KnowledgeService** (`knowledge_service.py`): Orchestrates embedding → search → rerank
  - Recipe CRUD and batch import
  - Configurable via `settings.KB_TOP_K`, `settings.RERANKER_PROVIDER`

#### 2. Knowledge Graph (`gustobot/infrastructure/knowledge/recipe_kg/`)

Neo4j-based structured recipe knowledge:

- **Entities**: Dish, Ingredient, Flavor, CookingMethod, DishType, CookingStep, NutritionProfile, HealthBenefit
- **Relationships**: HAS_MAIN_INGREDIENT, HAS_AUX_INGREDIENT, HAS_FLAVOR, USES_METHOD, BELONGS_TO_TYPE, HAS_STEP, HAS_NUTRITION_PROFILE, HAS_HEALTH_BENEFIT
- **Services**:
  - `graph_database_client.py`: Neo4j connection wrapper
  - `graph_importer_service.py`: Imports from JSON to Neo4j
  - `neo4j_qa_service.py`: Natural language → Cypher → Answer
  - `question_intent_classifier.py`: Classifies question intent for KG queries
  - `query_parser_service.py`: Extracts entities from questions
  - `answer_search_engine.py`: Executes Cypher and formats results

**Data Import Flow**:
1. `scripts/recipe_kg_to_csv.py` converts `data/recipe.json` + `data/excipients.json` → CSV
2. Docker build runs `neo4j-admin database import` to pre-seed database
3. Runtime bootstrap can also import via `NEO4J_BOOTSTRAP_JSON` setting

See `docs/recipe_kg_schema.md` for entity/relationship schema.

#### 3. GraphRAG (`gustobot/graphrag/`)

Microsoft GraphRAG integration for graph-based reasoning:

- `gustobot/graphrag/dev/graphrag_api.py`: FastAPI endpoints for GraphRAG queries
- `gustobot/graphrag/dev/graphrag_indexing.py`: Index building from documents
- `gustobot/graphrag/dev/graphrag_query.py`: Local/Global search modes
- `gustobot/graphrag/dev/graphrag_prompt_tune.py`: Prompt optimization

GraphRAG docs in `gustobot/graphrag/docs/` cover indexing, querying, configuration.

### Services Layer (`gustobot/services/`)

- **RedisSemanticCache**: LLM response caching using Ollama embeddings
  - Similarity-based cache lookup (configurable threshold)
  - Automatic cache invalidation and size limits
  - Namespace support for multi-tenant caching

- **RedisConversationHistory**: Persistent conversation storage
  - TTL-based expiration (default: 3 days)
  - Message limit per session (default: 200)
  - Async Redis operations

### Crawler Framework (`gustobot/crawler/`)

Extensible web scraping for recipe data collection:

- **BaseCrawler** (`base_crawler.py`): HTTP crawler with httpx
  - Proxy pool support, random User-Agent rotation
  - Configurable delays and retry logic

- **BrowserCrawler** (`browser_crawler.py`): Playwright-based automation
  - JavaScript rendering, scroll/click interactions
  - Anti-detection: WebDriver hiding, stealth mode

- **Implementations**:
  - `wikipedia_crawler.py`: Wikipedia recipe extraction
  - `recipe_crawler.py`: Schema.org standard recipe parsing
  - `recipe_browser_crawler.py`: Browser-based scraping example

- **Utilities**:
  - `proxy_pool.py`: Proxy rotation with health checks
  - `data_validator.py`: Pydantic-based validation
  - `cli.py`: Command-line interface for crawling

See `docs/crawler_guide.md`, `docs/crawler_examples.md`, `docs/anti_scraping_guide.md` for detailed usage.

### Configuration

`gustobot/config/settings.py` uses `pydantic-settings` to load from `.env`:

**Critical Settings**:
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`: LLM providers
- `OPENAI_MODEL` / `ANTHROPIC_MODEL`: Model selection
- `MILVUS_HOST/PORT/COLLECTION`: Vector database connection
- `EMBEDDING_MODEL/DIMENSION`: OpenAI embedding config
- `RERANKER_PROVIDER/API_KEY/MODEL`: Multi-provider reranking (cohere/jina/voyage/bge)
- `NEO4J_URI/USER/PASSWORD`: Knowledge graph connection
- `REDIS_URL`: Caching and conversation history
- `KB_TOP_K/SIMILARITY_THRESHOLD`: Retrieval parameters
- `OLLAMA_BASE_URL/EMBEDDING_MODEL`: Semantic cache embeddings

**Docker Services** (`docker-compose.yml`):
- `server`: FastAPI application (port 8000)
- `neo4j`: Pre-seeded graph database (ports 17474, 17687)
- `mysql`: Recipe relational data (port 13306)
- `redis`: Caching layer (port 6379)
- `milvus` + `etcd` + `minio`: Vector database stack (port 19530)

Neo4j is **pre-seeded during Docker build** via `neo4j-admin import` from CSV files generated by `scripts/recipe_kg_to_csv.py`.

### Data Flow for User Query

1. Frontend (`web/`) sends `POST /api/v1/chat/` to FastAPI server
2. **SupervisorAgent LangGraph Execution**:
   - `prepare_context` node: Loads recent conversation history from Redis
   - `check_cache` node: Semantic cache lookup (Ollama embeddings + Redis)
     - Cache hit → return cached answer immediately
     - Cache miss → continue to routing
   - `analyze_and_route_query`: LLM 路由节点（LangGraph）判定 `kb-query` / `general-query` / `graphrag-query` 等类型
   - Conditional edge routes to appropriate handler:
     - **kb-query** → `create_kb_query`：
       1. 调用 `create_kb_multi_tool_workflow`
       2. 按路由工具列表查询 Milvus、PostgreSQL（pgvector）与可选外部检索
       3. LangGraph Finalizer 汇总回答并收集来源
       4. 缓存结果（Redis 语义缓存）
     - **general-query** → `respond_to_general_query`：走轻量 LLM 闲聊/常识回答
     - **additional-query / research** → `create_research_plan` 等节点：生成后续任务或多跳计划
     - **reject** → `safety_refusal`: 直接输出礼貌拒绝
   - `save_history` node: Persist conversation to Redis with TTL
   - END: Return structured response with metadata (route, confidence, sources, cached flag)
3. Frontend displays answer with route indicator and sources

## Important Notes

- **Main Branch**: `develop` (not `main` or `master`)
- **Python Version**: Requires Python 3.9+
- **Directory Structure**:
  - `gustobot/` - Server code (NOT `backend/`)
  - `gustobot/application/agents/` - Multi-Agent system (LangGraph-based)
  - `gustobot/infrastructure/knowledge/` - Vector RAG components
  - `gustobot/infrastructure/knowledge/recipe_kg/` - Neo4j knowledge graph services
  - `gustobot/graphrag/` - GraphRAG integration
  - `gustobot/crawler/` - Web scraping framework
  - `gustobot/services/` - Redis caching, conversation history
  - `web/` - React frontend
  - `scripts/` - Data processing and VLLM deployment scripts
  - `docs/` - Comprehensive documentation
- **Multiple Knowledge Systems**: The project has THREE knowledge retrieval systems:
  1. Vector RAG (Milvus + Reranker) - primary for semantic search
  2. Knowledge Graph (Neo4j) - for structured recipe relationships
  3. GraphRAG - for graph-based reasoning
- **LangGraph State Management**: SupervisorAgent uses typed state with Pydantic models in `gustobot/application/agents/state_models.py`
- **Semantic Caching**: Uses Ollama for embeddings (NOT OpenAI) to reduce costs
- **Neo4j Bootstrap**: Graph database is pre-seeded during Docker build, not at runtime (unless `NEO4J_BOOTSTRAP_JSON=true`)
- **Testing**: Unit tests in `tests/unit/`, integration tests in `tests/integration/`

## Common Development Tasks

### Running the Full Stack Locally

1. **Configure environment**: `cp .env.example .env` and edit with your API keys
2. **Install dependencies**: `make install` (Python + Node.js)
3. **Start all services**: `make dev` (runs server + web concurrently)
   - Server: http://localhost:8000 (API docs at `/docs`)
   - Web: http://localhost:3000
4. **Docker mode**: `docker-compose up -d` (includes Neo4j, Redis, Milvus, MySQL)

### Working with Neo4j Knowledge Graph

**Rebuild graph from recipe JSON**:
```bash
# Regenerate CSV and rebuild Neo4j container
docker-compose build neo4j
docker-compose up -d neo4j
```

**Access Neo4j Browser**: http://localhost:17474 (auth disabled in dev)

**Query examples** (in Neo4j Browser):
```cypher
// Find dishes with specific ingredient
MATCH (d:Dish)-[:HAS_MAIN_INGREDIENT]->(i:Ingredient {name: "五花肉"})
RETURN d.name, i.name

// Get cooking steps for a dish
MATCH (d:Dish {name: "红烧肉"})-[:HAS_STEP]->(s:CookingStep)
RETURN s.order, s.instruction
ORDER BY s.order
```

### Adding Recipes to Vector Store

**Via crawler** (recommended):
```bash
python -m gustobot.crawler.cli wikipedia --query "川菜" --import-kb
python -m gustobot.crawler.cli urls --urls "https://example.com/recipe" --import-kb
```

**Via API**:
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/recipes" \
  -H "Content-Type: application/json" \
  -d '{"name": "红烧肉", "ingredients": ["五花肉500g"], ...}'
```

**Via Python script**:
```python
from gustobot.infrastructure.knowledge import KnowledgeService

service = KnowledgeService()
await service.add_recipe("recipe_001", {
    "name": "红烧肉",
    "category": "家常菜",
    "ingredients": ["五花肉500g", "冰糖30g"],
    "steps": ["切块", "焯水", "炒糖色"],
    "tips": "糖色不要炒过头"
})
```

### Working with LangGraph Agents

SupervisorAgent uses a state graph. To add a new node:

1. Define node function in `gustobot/application/agents/supervisor_agent.py`:
```python
async def my_custom_node(state: dict) -> dict:
    conv = ConversationState.model_validate(state)
    # Process state
    conv.custom_field = "value"
    return conv.to_dict()
```

2. Add node to graph in `_build_graph()`:
```python
graph.add_node("my_custom_node", my_custom_node)
graph.add_edge("previous_node", "my_custom_node")
```

3. Update `AgentState` definitions in `gustobot/application/agents/lg_states.py` if adding fields

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gustobot --cov-report=html

# Run single test module
pytest tests/test_agents_comprehensive.py -v
```

## Project Structure

```
GustoBot/
├── gustobot/                         # Server-side code
│   ├── agents/                    # LangGraph orchestrated nodes
│   │   ├── __init__.py
│   │   ├── lg_builder.py          # Supervisor / router graph
│   │   ├── lg_states.py           # Dataclass + TypedDict 状态
│   │   ├── lg_prompts.py          # Prompt 集中管理
│   │   ├── kb_tools/              # 知识库工具节点
│   │   ├── kg_sub_graph/          # Agentic RAG 多工具工作流
│   │   ├── text2sql/              # 结构化查询子图
│   │   ├── utils.py               # 通用工具函数
│   │   └── main.py                # CLI 入口
│   ├── knowledge_base/            # Knowledge systems
│   │   ├── vector_store.py        # Milvus wrapper
│   │   ├── embedding_service.py   # OpenAI embeddings
│   │   ├── reranker.py            # Multi-provider reranking
│   │   ├── knowledge_service.py   # Orchestration
│   │   └── recipe_kg/             # Neo4j knowledge graph
│   │       ├── graph_database_client.py
│   │       ├── neo4j_qa_service.py
│   │       └── (other KG services)
│   ├── graphrag/                  # GraphRAG integration
│   │   ├── dev/                   # GraphRAG server & tools
│   │   └── docs/                  # GraphRAG documentation
│   ├── crawler/                   # Web scraping framework
│   │   ├── base_crawler.py        # HTTP (httpx)
│   │   ├── browser_crawler.py     # Browser (Playwright)
│   │   ├── proxy_pool.py          # Proxy management
│   │   └── cli.py                 # CLI tool
│   ├── services/                  # Business services
│   │   ├── redis_semantic_cache.py
│   │   └── redis_conversation_history.py
│   ├── api/                       # FastAPI endpoints
│   ├── config/settings.py         # Pydantic settings
│   ├── core/                      # Core utilities
│   └── main.py                    # FastAPI app entry
├── web/                          # React frontend (Vite)
├── scripts/                      # Utility scripts
│   ├── recipe_kg_to_csv.py       # Neo4j CSV generation
│   └── vllm_start_*.sh           # VLLM deployment
├── tests/                        # Test suites
├── data/                         # Data (gitignored)
│   ├── recipe.json               # Recipe source
│   └── excipients.json           # Ingredient data
├── docs/                         # Documentation
│   ├── crawler_guide.md
│   ├── recipe_kg_schema.md
│   └── (other docs)
├── requirements.txt
├── Makefile
├── docker-compose.yml            # Neo4j, Redis, Milvus, MySQL
├── Dockerfile                    # Multi-stage (server + neo4j_seeded)
└── CLAUDE.md                     # This file
```

## Key File References

- **Multi-Agent coordination**: `gustobot/application/agents/supervisor_agent.py` (LangGraph state machine)
- **Agent state models**: `gustobot/application/agents/state_models.py` (Pydantic schemas)
- **Vector RAG**: `gustobot/infrastructure/knowledge/knowledge_service.py`
- **Neo4j KG**: `gustobot/infrastructure/knowledge/recipe_kg/neo4j_qa_service.py`
- **GraphRAG**: `gustobot/graphrag/dev/graphrag_api.py`
- **Semantic caching**: `gustobot/services/redis_semantic_cache.py`
- **Configuration**: `gustobot/config/settings.py`
- **Crawler CLI**: `gustobot/crawler/cli.py`
- **Neo4j import**: `scripts/recipe_kg_to_csv.py`
- **KG schema**: `docs/recipe_kg_schema.md`

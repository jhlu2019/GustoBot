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
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Or use: make run-server

# Run tests
pytest tests/ -v
# Or use: make test

# Code formatting and linting
black app/
flake8 app/ --max-line-length=100
mypy app/
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

# Add recipes via API (see app/api/knowledge.py for endpoints)
# POST /api/v1/knowledge/recipes
# POST /api/v1/knowledge/recipes/batch
```

## Architecture

### High-Level System Flow

```
User Query → SupervisorAgent (LangGraph) → Semantic Cache Check
                    ↓                              ↓ (cache miss)
            RouterAgent (LLM Classification)
                    ↓
        ┌───────────┼───────────┐
        │           │           │
  KnowledgeAgent  ChatAgent  RejectHandler
        ↓
  [Vector RAG | Neo4j KG | GraphRAG]
        ↓
  Cache Response → Return to User
```

### Multi-Agent System (LangGraph-based)

1. **SupervisorAgent** (`app/agents/supervisor_agent.py`) - LangGraph workflow coordinator
   - Builds state graph with nodes: prepare_context → check_cache → route → execute → save_history
   - Manages Redis conversation history and semantic caching
   - Implements conditional routing logic

2. **RouterAgent** (`app/agents/router_agent.py`) - LLM-based question classifier
   - Routes to: `knowledge` (recipe/cooking), `chat` (casual), `reject` (off-topic)
   - Uses structured prompts with conversation context
   - Returns route + confidence + reasoning

3. **KnowledgeAgent** (`app/agents/knowledge_agent.py`) - Hybrid knowledge retrieval
   - **Primary**: Vector RAG (Milvus search → Reranker → LLM generation)
   - **Optional**: Neo4j graph queries for structured relationships
   - **Optional**: GraphRAG for complex graph reasoning

4. **ChatAgent** (`app/agents/chat_agent.py`) - Conversational responses
   - LLM-powered friendly conversation
   - Template-based fallbacks

5. **State Management** (`app/agents/state_models.py`)
   - Pydantic models: ConversationInput, ConversationState, RouterResult, AgentAnswer
   - Type-safe state transitions across LangGraph nodes

### Knowledge Systems

The project implements **three complementary knowledge retrieval systems**:

#### 1. Vector RAG (`app/knowledge_base/`)

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

#### 2. Knowledge Graph (`app/knowledge_base/recipe_kg/`)

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

#### 3. GraphRAG (`app/graphrag/`)

Microsoft GraphRAG integration for graph-based reasoning:

- `app/graphrag/dev/graphrag_api.py`: FastAPI endpoints for GraphRAG queries
- `app/graphrag/dev/graphrag_indexing.py`: Index building from documents
- `app/graphrag/dev/graphrag_query.py`: Local/Global search modes
- `app/graphrag/dev/graphrag_prompt_tune.py`: Prompt optimization

GraphRAG docs in `app/graphrag/docs/` cover indexing, querying, configuration.

### Services Layer (`app/services/`)

- **RedisSemanticCache**: LLM response caching using Ollama embeddings
  - Similarity-based cache lookup (configurable threshold)
  - Automatic cache invalidation and size limits
  - Namespace support for multi-tenant caching

- **RedisConversationHistory**: Persistent conversation storage
  - TTL-based expiration (default: 3 days)
  - Message limit per session (default: 200)
  - Async Redis operations

### Crawler Framework (`app/crawler/`)

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

`app/config/settings.py` uses `pydantic-settings` to load from `.env`:

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
   - `route_node`: RouterAgent classifies question (LLM call)
   - Conditional edge routes to appropriate handler:
     - **knowledge** → `knowledge_node`:
       1. KnowledgeService: OpenAI embedding → Milvus search (top_k × 3)
       2. Reranker API (Cohere/Jina/Voyage/BGE) → top_k results
       3. Optional: Neo4j graph query for structured data
       4. LLM generates answer from retrieved documents
       5. Cache response in Redis semantic cache
     - **chat** → `chat_node`: ChatAgent LLM or template response
     - **reject** → `reject_node`: Polite rejection message
   - `save_history` node: Persist conversation to Redis with TTL
   - END: Return structured response with metadata (route, confidence, sources, cached flag)
3. Frontend displays answer with route indicator and sources

## Important Notes

- **Main Branch**: `develop` (not `main` or `master`)
- **Python Version**: Requires Python 3.9+
- **Directory Structure**:
  - `app/` - Server code (NOT `backend/`)
  - `app/agents/` - Multi-Agent system (LangGraph-based)
  - `app/knowledge_base/` - Vector RAG components
  - `app/knowledge_base/recipe_kg/` - Neo4j knowledge graph services
  - `app/graphrag/` - GraphRAG integration
  - `app/crawler/` - Web scraping framework
  - `app/services/` - Redis caching, conversation history
  - `web/` - React frontend
  - `scripts/` - Data processing and VLLM deployment scripts
  - `docs/` - Comprehensive documentation
- **Multiple Knowledge Systems**: The project has THREE knowledge retrieval systems:
  1. Vector RAG (Milvus + Reranker) - primary for semantic search
  2. Knowledge Graph (Neo4j) - for structured recipe relationships
  3. GraphRAG - for graph-based reasoning
- **LangGraph State Management**: SupervisorAgent uses typed state with Pydantic models in `app/agents/state_models.py`
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
python -m app.crawler.cli wikipedia --query "川菜" --import-kb
python -m app.crawler.cli urls --urls "https://example.com/recipe" --import-kb
```

**Via API**:
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/recipes" \
  -H "Content-Type: application/json" \
  -d '{"name": "红烧肉", "ingredients": ["五花肉500g"], ...}'
```

**Via Python script**:
```python
from app.knowledge_base import KnowledgeService

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

1. Define node function in `app/agents/supervisor_agent.py`:
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

3. Update `ConversationState` model in `app/agents/state_models.py` if adding fields

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_agents.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run single test
pytest tests/unit/test_agents.py::test_router_agent_initialization -v
```

## Project Structure

```
GustoBot/
├── app/                         # Server-side code
│   ├── agents/                    # Multi-Agent system (LangGraph)
│   │   ├── base_agent.py          # Agent base class
│   │   ├── supervisor_agent.py    # LangGraph coordinator (v1)
│   │   ├── supervisor_agent_v2.py # Alternative supervisor
│   │   ├── router_agent.py        # LLM-based classifier
│   │   ├── knowledge_agent.py     # Hybrid retrieval agent
│   │   ├── chat_agent.py          # Conversational agent
│   │   ├── state_models.py        # Pydantic state models
│   │   ├── nodes.py               # LangGraph node functions
│   │   └── kg_sub_graph/          # KG subgraph nodes
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

- **Multi-Agent coordination**: `app/agents/supervisor_agent.py` (LangGraph state machine)
- **Agent state models**: `app/agents/state_models.py` (Pydantic schemas)
- **Vector RAG**: `app/knowledge_base/knowledge_service.py`
- **Neo4j KG**: `app/knowledge_base/recipe_kg/neo4j_qa_service.py`
- **GraphRAG**: `app/graphrag/dev/graphrag_api.py`
- **Semantic caching**: `app/services/redis_semantic_cache.py`
- **Configuration**: `app/config/settings.py`
- **Crawler CLI**: `app/crawler/cli.py`
- **Neo4j import**: `scripts/recipe_kg_to_csv.py`
- **KG schema**: `docs/recipe_kg_schema.md`

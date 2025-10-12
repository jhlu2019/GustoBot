# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GustoBot** is an intelligent customer service chatbot for recipe recommendations and cooking assistance (菜谱智能客服). The project implements a Multi-Agent architecture to handle complex conversational AI tasks, including question routing, knowledge base retrieval, and conversational responses.

### Key Features

- **Multi-Agent Architecture**: Coordinated agents for routing, knowledge retrieval, and chat
- **RAG (Retrieval Augmented Generation)**: Vector database-backed knowledge retrieval
- **Smart Routing**: Automatically detects question relevance to recipes/cooking
- **Hallucination Prevention**: Only answers based on knowledge base content
- **Full-stack**: FastAPI server + React web frontend

## Development Commands

### Server (Backend)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run server (development mode)
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
# Or use: make run-server

# Run tests
pytest tests/ -v
# Or use: make test

# Code formatting and linting
black server/
flake8 server/ --max-line-length=100
mypy server/
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

# Add recipes via API (see server/api/knowledge.py for endpoints)
# POST /api/v1/knowledge/recipes
# POST /api/v1/knowledge/recipes/batch
```

## Architecture

### High-Level System Flow

```
User Query → SupervisorAgent → RouterAgent → [KnowledgeAgent | ChatAgent]
                    ↓
            Conversation History
```

1. **SupervisorAgent** (`server/agents/supervisor_agent.py`) - Orchestrates the entire flow
2. **RouterAgent** (`server/agents/router_agent.py`) - Classifies user questions:
   - `knowledge`: Recipe/cooking related → use knowledge base
   - `chat`: General conversation → friendly chat response
   - `reject`: Unrelated questions → polite rejection
3. **KnowledgeAgent** (`server/agents/knowledge_agent.py`) - RAG-based recipe assistant
4. **ChatAgent** (`server/agents/chat_agent.py`) - Handles casual conversation

### Multi-Agent Coordination

All agents inherit from `BaseAgent` (`server/agents/base_agent.py`) which provides:
- Common interface: `async def process(input_data: Dict) -> Dict`
- Logging utilities
- Input validation

The **SupervisorAgent** maintains conversation history and coordinates agent execution based on routing decisions.

### Knowledge Base System

Located in `server/knowledge_base/`:

- **VectorStore** (`vector_store.py`): Milvus vector database wrapper
  - Enterprise-grade vector search with IVF_FLAT indexing
  - Supports similarity search with Inner Product (IP) metric
  - Persistent storage via Milvus (requires docker-compose services)

- **EmbeddingService** (`embedding_service.py`): OpenAI Embedding API wrapper
  - Uses OpenAI's text-embedding-3-small model
  - 1536-dimensional vectors
  - Async API calls via OpenAI Python client

- **Reranker** (`reranker.py`): Multi-provider reranking service
  - Supports Cohere, Jina AI, Voyage AI, and BGE APIs
  - Two-stage retrieval: recall (Milvus) + rerank (API)
  - Provider-agnostic interface with configurable top_k

- **KnowledgeService** (`knowledge_service.py`): High-level knowledge operations
  - Recipe CRUD operations
  - Batch import functionality
  - Formatted document construction for optimal retrieval
  - Orchestrates: Embedding → Vector Search → Reranking

### API Structure

FastAPI endpoints in `server/api/`:

- **Chat API** (`chat.py`): Main conversational endpoint
  - `POST /api/v1/chat/` - Send user messages
  - `GET /api/v1/chat/status` - System status check

- **Knowledge API** (`knowledge.py`): Knowledge base management
  - `POST /api/v1/knowledge/recipes` - Add single recipe
  - `POST /api/v1/knowledge/recipes/batch` - Bulk import
  - `POST /api/v1/knowledge/search` - Direct search
  - `DELETE /api/v1/knowledge/recipes/{id}` - Delete recipe
  - `GET /api/v1/knowledge/stats` - Knowledge base statistics

### Frontend Architecture

React + Vite application in `web/`:

- **ChatInterface** (`src/components/ChatInterface.jsx`): Main chat UI
- **Message** (`src/components/Message.jsx`): Individual message rendering with markdown support
- **API Service** (`src/services/api.js`): Axios-based API client with interceptors

API proxy configured in `vite.config.js` to route `/api` to server.

### Configuration

- **Server Config**: `server/config/settings.py` using `pydantic-settings`
  - Environment-based configuration via `.env`
  - LLM API keys (OpenAI/Anthropic)
  - Milvus vector database settings (host, port, collection, index type)
  - OpenAI Embedding configuration (model, dimensions)
  - Reranker configuration (provider, API key, model, API URL for BGE)
  - Agent parameters (timeouts, iterations, similarity thresholds)

- **Environment Variables**: See `.env.example` for required variables
  - Required: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
  - Required for embedding: `OPENAI_API_KEY` (for text-embedding-3-small)
  - Required for reranking: `RERANKER_API_KEY` (provider-specific)
  - Optional: Milvus connection details (defaults to localhost:19530)

### Data Flow for User Query

1. User sends message via web frontend
2. Frontend calls `POST /api/v1/chat/`
3. SupervisorAgent receives request with session context
4. RouterAgent classifies the question using LLM or rule-based logic
5. Based on route:
   - **knowledge**: KnowledgeAgent uses two-stage retrieval:
     1. Embed query with OpenAI API
     2. Recall candidates from Milvus (top_k * 3)
     3. Rerank with API provider (Cohere/Jina/Voyage/BGE)
     4. Generate answer from top reranked docs
   - **chat**: ChatAgent provides friendly template or LLM response
   - **reject**: Return polite rejection
6. Response includes metadata (route type, confidence, sources)
7. SupervisorAgent logs conversation history
8. Frontend displays answer with route indicator

## Important Notes

- **Main Branch**: `develop` (not `main` or `master`)
- **Python Version**: Requires Python 3.9+
- **Directory Structure**:
  - `server/` - Backend/server code (NOT `backend/`)
  - `web/` - Frontend code (NOT `frontend/`)
  - `Dockerfile` - Server dockerfile (no `.backend` suffix)
- **LLM Integration**: Currently has placeholder methods for LLM calls. Implement in:
  - `RouterAgent._call_llm()` for question classification
  - `KnowledgeAgent._call_llm()` for RAG answer generation
  - `ChatAgent._call_llm()` for conversational responses
- **Dependencies**: All agents depend on properly initialized services (VectorStore, LLM clients)
- **Testing**: Unit tests in `tests/unit/` - run with `pytest`
- **Dependency Injection**: API endpoints use FastAPI's `Depends()` for agent initialization

## Common Development Tasks

### Adding a New Agent

1. Create agent class in `server/agents/` inheriting from `BaseAgent`
2. Implement `async def process(input_data: Dict) -> Dict`
3. Register in `server/agents/__init__.py`
4. Add to SupervisorAgent initialization
5. Update routing logic if needed

### Adding Recipes to Knowledge Base

Use the API or create a script:

```python
from server.knowledge_base import KnowledgeService

service = KnowledgeService()
await service.add_recipe("recipe_001", {
    "name": "红烧肉",
    "category": "家常菜",
    "ingredients": ["五花肉500g", "冰糖30g"],
    "steps": ["切块", "焯水", "炒糖色"],
    "tips": "糖色不要炒过头"
})
```

### Implementing LLM Integration

Replace `raise NotImplementedError("LLM integration pending")` in agent files with actual API calls:

```python
# Example for OpenAI
from openai import AsyncOpenAI
from server.config import settings

async def _call_llm(self, system_prompt: str, user_message: str) -> str:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content
```

### Running the Full Stack Locally

1. Copy `.env.example` to `.env` and configure
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `make install`
5. Initialize data directories: `make init-data`
6. Run both services: `make dev`
7. Access web at `http://localhost:3000`
8. API docs at `http://localhost:8000/docs`

## Project Structure

```
GustoBot/
├── server/                    # Server-side code
│   ├── agents/               # Multi-Agent system
│   │   ├── base_agent.py     # Agent base class
│   │   ├── router_agent.py   # Routing agent
│   │   ├── knowledge_agent.py # Knowledge base agent
│   │   ├── chat_agent.py     # Chat agent
│   │   └── supervisor_agent.py # Supervisor agent
│   ├── api/                  # FastAPI endpoints
│   │   ├── chat.py           # Chat API
│   │   └── knowledge.py      # Knowledge base API
│   ├── knowledge_base/       # Knowledge base module
│   │   ├── vector_store.py   # Milvus vector DB wrapper
│   │   ├── embedding_service.py # OpenAI Embedding API
│   │   ├── reranker.py       # Multi-provider reranking
│   │   └── knowledge_service.py # Knowledge service orchestrator
│   ├── config/               # Configuration
│   │   └── settings.py       # Settings class
│   └── main.py               # Application entry point
├── web/                      # Web frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API services
│   │   └── App.jsx           # Root component
│   └── package.json
├── tests/                    # Tests
│   └── unit/
├── data/                     # Data directory (gitignored)
│   └── milvus/              # Milvus persistence (via docker volumes)
├── requirements.txt          # Python dependencies
├── Makefile                 # Development commands
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker orchestration
└── CLAUDE.md                # This file
```

## Common Pitfalls

1. **Import Paths**: Always use `server.*` not `backend.*` in imports
2. **Docker**: Dockerfile is named `Dockerfile` not `Dockerfile.backend`
3. **Make Commands**: Use `run-server` and `run-web` not `run-backend` and `run-frontend`
4. **Directory Names**: `server/` and `web/` are the correct directory names

## File References

When working with the codebase, key file locations:

- Agent implementations: `server/agents/`
- API routes: `server/api/`
- Knowledge base: `server/knowledge_base/`
- Configuration: `server/config/settings.py`
- Frontend components: `web/src/components/`
- Tests: `tests/unit/`

"""
Centralised application settings for GustoBot.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application wide configuration loaded from environment variables."""

    # Application metadata
    APP_NAME: str = "GustoBot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # OpenAI models
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Anthropic models
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Vision models (for image analysis)
    VISION_API_KEY: Optional[str] = None
    VISION_BASE_URL: Optional[str] = None
    VISION_MODEL: str = "gpt-4-vision-preview"

    # Milvus vector database
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "recipes"
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    MILVUS_METRIC_TYPE: str = "IP"

    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # Reranker
    RERANKER_PROVIDER: str = "cohere"
    RERANKER_API_KEY: Optional[str] = None
    RERANKER_MODEL: Optional[str] = None
    RERANKER_API_URL: Optional[str] = None
    RERANKER_TOP_K: int = 5

    # Web search tooling
    SERPAPI_KEY: Optional[str] = None
    SERPAPI_BASE_URL: str = Field(
        default="https://serpapi.com/search",
        description="Base URL for SerpAPI requests",
    )
    SERPAPI_TIMEOUT: float = Field(
        default=15.0,
        description="SerpAPI request timeout in seconds",
    )
    SEARCH_RESULT_COUNT: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Default number of search results to return",
    )

    # Redis cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URI",
    )
    REDIS_CACHE_EXPIRE: int = Field(
        default=60 * 60 * 12,
        description="Redis cache expiry in seconds",
    )
    REDIS_CACHE_THRESHOLD: float = Field(
        default=0.92,
        description="Semantic cache similarity threshold",
    )
    REDIS_CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="Maximum number of cached items per namespace",
    )

    # Relational database
    DATABASE_URL: str = "sqlite:///./data/gustobot.db"

    # LightRAG configuration
    LIGHTRAG_WORKING_DIR: str = Field(
        default="./data/lightrag",
        description="LightRAG 工作目录，用于存储索引和缓存"
    )
    LIGHTRAG_RETRIEVAL_MODE: str = Field(
        default="hybrid",
        description="LightRAG 检索模式: local, global, hybrid, naive, mix, bypass"
    )
    LIGHTRAG_TOP_K: int = Field(
        default=10,
        description="LightRAG 检索返回的top-k结果数量"
    )
    LIGHTRAG_MAX_TOKEN_SIZE: int = Field(
        default=4096,
        description="LightRAG 文本单元的最大token数量"
    )
    LIGHTRAG_ENABLE_NEO4J: bool = Field(
        default=True,
        description="是否使用Neo4j作为LightRAG的图存储后端"
    )
    LIGHTRAG_ENABLE_MILVUS: bool = Field(
        default=False,
        description="是否使用Milvus作为LightRAG的向量存储后端（默认使用内置向量存储）"
    )

    # Neo4j configuration
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_DEFAULT_GRAPH_QUERY: str = "MATCH (a)-[r]-(b) RETURN a, r, b LIMIT 100"
    NEO4J_GRAPH_CACHE_PATH: str = "data/neo4j/graph.json"
    NEO4J_MAX_CONNECTION_LIFETIME: Optional[int] = None
    NEO4J_BOOTSTRAP_JSON: bool = True
    NEO4J_BOOTSTRAP_FORCE: bool = False
    NEO4J_RECIPE_JSON_PATH: str = "data/recipe.json"
    NEO4J_INGREDIENT_JSON_PATH: Optional[str] = "data/excipients.json"

    # Agent behaviour
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300

    # Knowledge base retrieval
    KB_TOP_K: int = 5
    KB_SIMILARITY_THRESHOLD: float = 0.7
    KB_CHUNK_SIZE: int = Field(
        default=512,
        description="Chunk size used when splitting documents for the knowledge base",
    )
    KB_CHUNK_OVERLAP: int = Field(
        default=80,
        description="Chunk overlap used when splitting documents",
    )

    # External ingestion service (test folder FastAPI) configuration
    INGEST_SERVICE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for external ingestion service (e.g., http://localhost:8000)",
    )
    FILE_UPLOAD_MAX_MB: int = Field(
        default=2,
        ge=1,
        description="Maximum accepted upload file size in MB for local ingestion",
    )
    ENABLE_EXTERNAL_SEARCH: bool = Field(
        default=False,
        description="Whether tools are allowed to perform external network search",
    )
    KB_ENABLE_EXTERNAL_SEARCH: bool = Field(
        default=False,
        description="Augment KB answers with optional external web search",
    )

    # Conversation history retention
    CONVERSATION_HISTORY_TTL: int = Field(
        default=60 * 60 * 24 * 3,
        description="How long to retain chat history in seconds",
    )
    CONVERSATION_HISTORY_MAX_MESSAGES: int = Field(
        default=200,
        description="Maximum number of messages retained per conversation",
    )

    # CORS
    CORS_ORIGINS: Tuple[str, ...] = (
        "http://localhost:3000",
        "http://localhost:5173",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def NEO4J_USERNAME(self) -> Optional[str]:  # pragma: no cover - convenience alias
        return self.NEO4J_USER


settings = Settings()

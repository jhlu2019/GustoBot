"""
应用配置管理
Configuration Management
"""
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "GustoBot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API配置
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Anthropic配置
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Milvus向量数据库配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "recipes"
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"  # IVF_FLAT, IVF_SQ8, HNSW
    MILVUS_METRIC_TYPE: str = "IP"  # IP (Inner Product), L2, COSINE

    # OpenAI Embedding配置
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # Reranker配置
    RERANKER_PROVIDER: str = "cohere"  # cohere, jina, voyage, bge
    RERANKER_API_KEY: Optional[str] = None
    RERANKER_MODEL: Optional[str] = None  # 留空使用默认模型
    RERANKER_API_URL: Optional[str] = None  # BGE provider需要
    RERANKER_TOP_K: int = 5

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/gustobot.db"

    # Agent配置
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300  # 秒

    # 知识库配置
    KB_TOP_K: int = 5
    KB_SIMILARITY_THRESHOLD: float = 0.7

    # CORS配置
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

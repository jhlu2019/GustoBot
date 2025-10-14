"""
应用配置管理
Configuration Management
"""
from typing import Optional, List, Tuple
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
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    REDIS_CACHE_EXPIRE: int = Field(
        default=60 * 60 * 12,
        description="Redis缓存过期时间（秒）"
    )
    REDIS_CACHE_THRESHOLD: float = Field(
        default=0.92,
        description="语义缓存命中相似度阈值"
    )
    REDIS_CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="单个命名空间的最大缓存条目数"
    )

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/gustobot.db"

    # Agent配置
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300  # 秒

    # 知识库配置
    KB_TOP_K: int = 5
    KB_SIMILARITY_THRESHOLD: float = 0.7

    # 对话历史配置
    CONVERSATION_HISTORY_TTL: int = Field(
        default=60 * 60 * 24 * 3,
        description="对话历史在Redis中的保留时间（秒）"
    )
    CONVERSATION_HISTORY_MAX_MESSAGES: int = Field(
        default=200,
        description="每个会话保留的最大消息数"
    )

    # CORS配置
    CORS_ORIGINS: Tuple[str, ...] = (
        "http://localhost:3000",
        "http://localhost:5173",
    )



    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

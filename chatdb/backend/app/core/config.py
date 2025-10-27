import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    MYSQL_SERVER: str = os.getenv("MYSQL_SERVER", "localhost")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "mysql")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "chatdb")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")

    # Neo4j settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://155.138.220.75:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "65132090")

    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "sk-04d0650a86124b31be03bb6c7bbaa036")
    OPENAI_API_BASE: Optional[str] = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # Milvus配置
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT", "19530")

    # 向量模型配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))

    # 混合检索配置
    HYBRID_RETRIEVAL_ENABLED: bool = os.getenv("HYBRID_RETRIEVAL_ENABLED", "true").lower() == "true"
    SEMANTIC_WEIGHT: float = float(os.getenv("SEMANTIC_WEIGHT", "0.35"))
    STRUCTURAL_WEIGHT: float = float(os.getenv("STRUCTURAL_WEIGHT", "0.35"))
    PATTERN_WEIGHT: float = float(os.getenv("PATTERN_WEIGHT", "0.20"))
    QUALITY_WEIGHT: float = float(os.getenv("QUALITY_WEIGHT", "0.10"))

    # 学习配置
    AUTO_LEARNING_ENABLED: bool = os.getenv("AUTO_LEARNING_ENABLED", "true").lower() == "true"
    FEEDBACK_LEARNING_ENABLED: bool = os.getenv("FEEDBACK_LEARNING_ENABLED", "true").lower() == "true"
    PATTERN_DISCOVERY_ENABLED: bool = os.getenv("PATTERN_DISCOVERY_ENABLED", "true").lower() == "true"

    # 性能配置
    RETRIEVAL_CACHE_TTL: int = int(os.getenv("RETRIEVAL_CACHE_TTL", "3600"))
    MAX_EXAMPLES_PER_QUERY: int = int(os.getenv("MAX_EXAMPLES_PER_QUERY", "5"))
    PARALLEL_RETRIEVAL: bool = os.getenv("PARALLEL_RETRIEVAL", "true").lower() == "true"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

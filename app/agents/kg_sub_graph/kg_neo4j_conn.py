from langchain_neo4j import Neo4jGraph
from app.config import settings
from app.core.logger import get_logger
import logging

# 获取日志记录器
logger = get_logger(service="kg_builder")

# 设置Neo4j驱动的日志级别为ERROR，禁止WARNING消息
logging.getLogger("neo4j").setLevel(logging.ERROR)
# 禁用langchain_neo4j相关日志
logging.getLogger("langchain_neo4j").setLevel(logging.ERROR)
# 禁用驱动相关日志
logging.getLogger("neo4j.io").setLevel(logging.ERROR)
logging.getLogger("neo4j.bolt").setLevel(logging.ERROR)

def get_neo4j_graph() -> Neo4jGraph:
    """
    创建并返回一个Neo4jGraph实例，使用配置文件中的设置。
    
    Returns:
        Neo4jGraph: 配置好的Neo4j图数据库连接实例
    """
    logger.info(f"initialize Neo4j connection: {settings.NEO4J_URI}")

    try:
        kwargs = {
            "url": settings.NEO4J_URI,
            "database": settings.NEO4J_DATABASE,
        }
        if settings.NEO4J_USER and settings.NEO4J_PASSWORD not in (None, ""):
            kwargs.update({
                "username": settings.NEO4J_USER,
                "password": settings.NEO4J_PASSWORD,
            })
        
        neo4j_graph = Neo4jGraph(**kwargs)
        return neo4j_graph
    except Exception as e:
        raise

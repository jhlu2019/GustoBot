"""
LightRAG 查询节点
使用 LightRAG 替代 Microsoft GraphRAG，提供轻量级、高效的图谱检索能力
"""
from typing import Any, Callable, Coroutine, Dict, List, Optional
import asyncio
import os
from pathlib import Path
from pydantic import BaseModel, Field
from lightrag import LightRAG, QueryParam
from lightrag.kg.neo4j_impl import Neo4JStorage
LIGHTRAG_AVAILABLE = True

# 导入配置
from app.config import settings
from app.core.logger import get_logger

logger = get_logger(service="lightrag-node")


# 定义 LightRAG 查询的输入状态类型
class LightRAGQueryInputState(BaseModel):
    task: str
    query: str
    steps: List[str] = Field(...)


# 定义 LightRAG 查询的输出状态类型
class LightRAGQueryOutputState(BaseModel):
    task: str
    query: str
    statement: str = Field(default="")
    parameters: str = Field(default="")
    errors: List[str] = Field(...)
    records: Dict[str, Any] = Field(...)
    steps: List[str] = Field(...)


# 定义 LightRAG API 包装器
class LightRAGAPI:
    """
    LightRAG API 封装类

    功能:
    - 轻量级图谱检索（相比 Microsoft GraphRAG 减少 99% token 消耗）
    - 支持多种检索模式: local, global, hybrid, naive
    - 可选集成 Neo4j 作为图存储后端
    - 支持增量文档更新
    """

    def __init__(
        self,
        working_dir: Optional[str] = None,
        retrieval_mode: Optional[str] = None,
        top_k: Optional[int] = None,
        max_token_size: Optional[int] = None,
        enable_neo4j: Optional[bool] = None,
    ):
        """
        初始化 LightRAG API

        Parameters
        ----------
        working_dir : str, optional
            LightRAG 工作目录
        retrieval_mode : str, optional
            检索模式: local, global, hybrid, naive, mix, bypass
        top_k : int, optional
            返回的 top-k 结果数量
        max_token_size : int, optional
            文本单元的最大 token 数量
        enable_neo4j : bool, optional
            是否使用 Neo4j 作为图存储后端
        """
        if not LIGHTRAG_AVAILABLE:
            raise ImportError("LightRAG 未安装，请运行 'pip install lightrag-hku'")

        # 从环境变量获取配置，如果提供了参数则使用参数值
        self.working_dir = working_dir or settings.LIGHTRAG_WORKING_DIR
        self.retrieval_mode = retrieval_mode or settings.LIGHTRAG_RETRIEVAL_MODE
        self.top_k = top_k or settings.LIGHTRAG_TOP_K
        self.max_token_size = max_token_size or settings.LIGHTRAG_MAX_TOKEN_SIZE
        self.enable_neo4j = enable_neo4j if enable_neo4j is not None else settings.LIGHTRAG_ENABLE_NEO4J

        self.rag: Optional[LightRAG] = None
        self.initialized = False

    async def initialize(self):
        """初始化 LightRAG 实例"""
        if self.initialized:
            return
        try:
            # 确保工作目录存在
            os.makedirs(self.working_dir, exist_ok=True)

            # 配置图存储后端
            graph_storage = None
            if self.enable_neo4j and settings.NEO4J_URI:
                try:
                    logger.info("使用 Neo4j 作为 LightRAG 图存储后端")
                    graph_storage = Neo4JStorage(
                        uri=settings.NEO4J_URI,
                        user=settings.NEO4J_USER,
                        password=settings.NEO4J_PASSWORD,
                        database=settings.NEO4J_DATABASE
                    )
                except Exception as e:
                    logger.warning(f"Neo4j 连接失败，使用默认图存储: {e}")
                    graph_storage = None

            # 创建 LightRAG 实例
            logger.info(f"初始化 LightRAG，工作目录: {self.working_dir}")
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_name=settings.OPENAI_MODEL,
                llm_model_kwargs={
                    "api_key": settings.OPENAI_API_KEY,
                    "base_url": settings.OPENAI_API_BASE,
                    "model": settings.OPENAI_MODEL
                },
                embedding_model_name=settings.EMBEDDING_MODEL,
                embedding_model_kwargs={
                    "api_key": settings.OPENAI_API_KEY,
                    "base_url": settings.OPENAI_API_BASE
                },
                graph_storage=graph_storage,
            )

            # 初始化存储
            await self.rag.initialize_storages()

            self.initialized = True
            logger.info("LightRAG 初始化成功")

        except Exception as e:
            logger.error(f"初始化 LightRAG 时出错: {str(e)}", exc_info=True)
            raise Exception(f"LightRAG 初始化失败: {str(e)}")

    async def query(self, query: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        执行 LightRAG 查询

        Parameters
        ----------
        query : str
            查询文本
        mode : str, optional
            检索模式，如果不指定则使用默认配置

        Returns
        -------
        Dict[str, Any]
            查询结果，包含 response 和 mode
        """
        await self.initialize()

        retrieval_mode = mode or self.retrieval_mode

        try:
            logger.info(f"执行 LightRAG 查询，模式: {retrieval_mode}")
            logger.info(f"查询内容: {query}")

            # 创建查询参数
            param = QueryParam(
                mode=retrieval_mode,
                top_k=self.top_k,
                max_token_for_text_unit=self.max_token_size,
            )

            # 执行查询
            response = await self.rag.aquery(query, param=param)

            logger.info(f"LightRAG 查询成功，响应长度: {len(response)} 字符")

            return {
                "response": response,
                "mode": retrieval_mode,
                "query": query
            }

        except Exception as e:
            logger.error(f"执行 LightRAG 查询时出错: {str(e)}", exc_info=True)
            raise Exception(f"LightRAG 查询失败: {str(e)}")

    async def insert_documents(self, documents: List[str]) -> Dict[str, Any]:
        """
        批量插入文档到 LightRAG

        Parameters
        ----------
        documents : List[str]
            要插入的文档列表

        Returns
        -------
        Dict[str, Any]
            插入结果统计
        """
        await self.initialize()

        try:
            logger.info(f"开始插入 {len(documents)} 个文档")

            success_count = 0
            error_count = 0

            for i, doc in enumerate(documents):
                try:
                    await self.rag.ainsert(doc)
                    success_count += 1
                    if (i + 1) % 10 == 0:
                        logger.info(f"已插入 {i + 1}/{len(documents)} 个文档")
                except Exception as e:
                    error_count += 1
                    logger.error(f"插入文档 {i + 1} 失败: {e}")

            logger.info(f"文档插入完成，成功: {success_count}，失败: {error_count}")

            return {
                "total": len(documents),
                "success": success_count,
                "error": error_count
            }

        except Exception as e:
            logger.error(f"批量插入文档时出错: {str(e)}", exc_info=True)
            raise Exception(f"文档插入失败: {str(e)}")


def create_lightrag_query_node(
) -> Callable[
    [Dict[str, Any]],
    Coroutine[Any, Any, Dict[str, List[LightRAGQueryOutputState] | List[str]]],
]:
    """
    创建 LightRAG 查询节点，用于 LangGraph 工作流

    相比 Microsoft GraphRAG:
    - 体积减少 94%（1.7GB → < 100MB）
    - Token 消耗减少 99%
    - 支持增量更新
    - API 更简洁

    Returns
    -------
    Callable[[Dict[str, Any]], Dict[str, List[LightRAGQueryOutputState] | List[str]]]
        名为 `lightrag_query` 的 LangGraph 节点
    """

    async def lightrag_query(
        state: Dict[str, Any],
    ) -> Dict[str, List[LightRAGQueryOutputState] | List[str]]:
        """
        执行 LightRAG 查询并返回结果
        """
        errors = []
        search_result = {}

        # 获取查询文本
        query = state.get("task", "")
        if not query:
            errors.append("未提供查询文本")
        else:
            try:
                # 创建 LightRAG API 实例
                lightrag_api = LightRAGAPI()

                # 调用 LightRAG API 获取数据
                search_result = await lightrag_api.query(query)

            except Exception as e:
                errors.append(f"LightRAG 查询失败: {str(e)}")
                logger.error(f"LightRAG 查询节点执行失败: {str(e)}", exc_info=True)

        return {
            "cyphers": [
                LightRAGQueryOutputState(
                    **{
                        "task": state.get("task", ""),
                        "query": query,
                        "statement": f"LightRAG {search_result.get('mode', '')} search",
                        "parameters": "",
                        "errors": errors,
                        "records": {"result": search_result.get("response", "")},
                        "steps": ["execute_lightrag_query"],
                    }
                )
            ],
            "steps": ["execute_lightrag_query"],
        }

    return lightrag_query


# 向后兼容：保留原有的函数名
create_graphrag_query_node = create_lightrag_query_node
GraphRAGAPI = LightRAGAPI

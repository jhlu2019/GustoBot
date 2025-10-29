"""
LightRAG 问答检索服务

基于 Docker build 时生成的 LightRAG JSON 文件提供问答检索功能
- 使用预生成的索引文件（kv_store_*.json, vdb_*.json, graph_chunk_entity_relation.graphml）
- 支持多种检索模式：naive, local, global, hybrid
- 支持流式响应
- 支持增量文档插入
"""

import os
import asyncio
import inspect
from typing import AsyncGenerator, Dict, Any, List, Optional, Literal
from pathlib import Path

from pydantic import BaseModel, Field
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
import numpy as np

from gustobot.config import settings
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="lightrag-service")

# 检索模式类型
SearchMode = Literal["naive", "local", "global", "hybrid", "mix", "bypass"]


class LightRAGQueryRequest(BaseModel):
    """LightRAG 查询请求"""
    query: str = Field(..., description="查询问题")
    mode: SearchMode = Field(default="hybrid", description="检索模式")
    top_k: Optional[int] = Field(default=None, description="返回结果数量，None 则使用默认配置")
    stream: bool = Field(default=False, description="是否使用流式响应")


class LightRAGQueryResponse(BaseModel):
    """LightRAG 查询响应"""
    query: str = Field(..., description="原始查询")
    response: str = Field(..., description="回答内容")
    mode: SearchMode = Field(..., description="使用的检索模式")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class LightRAGInsertRequest(BaseModel):
    """LightRAG 文档插入请求"""
    documents: List[str] = Field(..., description="要插入的文档列表")


class LightRAGInsertResponse(BaseModel):
    """LightRAG 文档插入响应"""
    total: int = Field(..., description="总文档数")
    success: int = Field(..., description="成功插入数")
    failed: int = Field(..., description="失败数")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class LightRAGService:
    """
    LightRAG 问答检索服务

    功能：
    - 基于预生成的索引文件进行问答检索
    - 支持多种检索模式（naive, local, global, hybrid）
    - 支持流式和非流式响应
    - 支持增量文档插入
    """

    def __init__(
        self,
        working_dir: Optional[str] = None,
        default_mode: SearchMode = "hybrid",
        default_top_k: int = 10,
    ):
        """
        初始化 LightRAG 服务

        Parameters
        ----------
        working_dir : str, optional
            LightRAG 工作目录（包含预生成的 JSON 文件）
        default_mode : SearchMode, optional
            默认检索模式
        default_top_k : int, optional
            默认返回结果数量
        """
        self.working_dir = working_dir or settings.LIGHTRAG_WORKING_DIR
        self.default_mode = default_mode
        self.default_top_k = default_top_k

        self.rag: Optional[LightRAG] = None
        self.initialized = False

        logger.info(f"LightRAG 服务初始化，工作目录: {self.working_dir}")

    async def _llm_model_func(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: List = [],
        **kwargs
    ) -> str:
        """
        LLM 模型函数

        Parameters
        ----------
        prompt : str
            用户提示词
        system_prompt : str, optional
            系统提示词
        history_messages : list, optional
            历史消息
        **kwargs : dict
            其他参数

        Returns
        -------
        str
            LLM 生成的文本
        """
        return await openai_complete_if_cache(
            model=settings.OPENAI_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            **kwargs,
        )

    async def _embedding_func(self, texts: List[str]) -> np.ndarray:
        """
        Embedding 函数

        Parameters
        ----------
        texts : List[str]
            要嵌入的文本列表

        Returns
        -------
        np.ndarray
            嵌入向量数组
        """
        return await openai_embed(
            texts=texts,
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )

    async def initialize(self) -> None:
        """
        初始化 LightRAG 实例

        会检查工作目录是否存在预生成的索引文件：
        - graph_chunk_entity_relation.graphml
        - kv_store_*.json
        - vdb_*.json
        """
        if self.initialized:
            logger.info("LightRAG 已初始化，跳过")
            return

        try:
            # 检查工作目录
            if not os.path.exists(self.working_dir):
                logger.warning(f"工作目录不存在，创建: {self.working_dir}")
                os.makedirs(self.working_dir, exist_ok=True)

            # 检查预生成的索引文件
            required_files = [
                "graph_chunk_entity_relation.graphml",
                "kv_store_doc_status.json",
                "kv_store_full_docs.json",
                "kv_store_text_chunks.json",
                "vdb_chunks.json",
                "vdb_entities.json",
                "vdb_relationships.json",
            ]

            missing_files = []
            for file_name in required_files:
                file_path = os.path.join(self.working_dir, file_name)
                if not os.path.exists(file_path):
                    missing_files.append(file_name)

            if missing_files:
                logger.warning(
                    f"警告：以下索引文件不存在，查询可能返回空结果:\n"
                    f"{', '.join(missing_files)}\n"
                    f"请确保 Docker build 时已正确初始化 LightRAG"
                )
            else:
                logger.info("✓ 所有预生成的索引文件已存在")
                # 显示文件大小
                for file_name in required_files:
                    file_path = os.path.join(self.working_dir, file_name)
                    file_size = os.path.getsize(file_path)
                    logger.info(f"  - {file_name}: {file_size / 1024:.2f} KB")

            # 获取 embedding 维度
            embedding_dim = int(settings.EMBEDDING_DIMENSION or 1536)
            logger.info(f"Embedding 维度: {embedding_dim}")
            logger.info(f"LLM 模型: {settings.OPENAI_MODEL}")
            logger.info(f"Embedding 模型: {settings.EMBEDDING_MODEL}")

            # 创建 LightRAG 实例
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=self._llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=embedding_dim,
                    max_token_size=settings.LIGHTRAG_MAX_TOKEN_SIZE,
                    func=self._embedding_func,
                ),
            )

            # 初始化存储（会加载预生成的索引文件）
            logger.info("加载预生成的索引文件...")
            await self.rag.initialize_storages()
            await initialize_pipeline_status()

            self.initialized = True
            logger.info("✓ LightRAG 服务初始化成功")

        except Exception as e:
            logger.error(f"初始化 LightRAG 服务失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"LightRAG 初始化失败: {str(e)}")

    async def query(
        self,
        query: str,
        mode: Optional[SearchMode] = None,
        top_k: Optional[int] = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        执行问答检索

        Parameters
        ----------
        query : str
            查询问题
        mode : SearchMode, optional
            检索模式（naive/local/global/hybrid），默认使用配置的模式
        top_k : int, optional
            返回结果数量，默认使用配置的值
        stream : bool, optional
            是否使用流式响应

        Returns
        -------
        str | AsyncGenerator[str, None]
            如果 stream=False，返回完整答案字符串
            如果 stream=True，返回异步生成器
        """
        await self.initialize()

        retrieval_mode = mode or self.default_mode
        k = top_k or self.default_top_k

        try:
            logger.info(f"执行查询 | 模式: {retrieval_mode} | Top-K: {k}")
            logger.info(f"查询内容: {query}")

            # 创建查询参数
            param = QueryParam(
                mode=retrieval_mode,
                top_k=k,
                stream=stream,
            )

            # 执行查询
            response = await self.rag.aquery(query, param=param)

            # 如果是流式响应，返回生成器
            if stream and inspect.isasyncgen(response):
                logger.info("返回流式响应")
                return response
            else:
                logger.info(f"查询成功 | 响应长度: {len(response)} 字符")
                return response

        except Exception as e:
            logger.error(f"查询失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"LightRAG 查询失败: {str(e)}")

    async def query_structured(
        self,
        request: LightRAGQueryRequest
    ) -> LightRAGQueryResponse:
        """
        执行结构化查询（非流式）

        Parameters
        ----------
        request : LightRAGQueryRequest
            查询请求

        Returns
        -------
        LightRAGQueryResponse
            结构化查询响应
        """
        response = await self.query(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k,
            stream=False,
        )

        return LightRAGQueryResponse(
            query=request.query,
            response=response,
            mode=request.mode,
            metadata={
                "top_k": request.top_k or self.default_top_k,
                "working_dir": self.working_dir,
            }
        )

    async def insert_documents(
        self,
        documents: List[str],
        batch_size: int = 10,
    ) -> LightRAGInsertResponse:
        """
        增量插入文档到 LightRAG

        Parameters
        ----------
        documents : List[str]
            要插入的文档列表
        batch_size : int, optional
            批量处理大小（每处理 batch_size 个文档记录一次进度）

        Returns
        -------
        LightRAGInsertResponse
            插入结果统计
        """
        await self.initialize()

        try:
            logger.info(f"开始插入 {len(documents)} 个文档")

            success_count = 0
            failed_count = 0
            errors = []

            for i, doc in enumerate(documents):
                try:
                    await self.rag.ainsert(doc)
                    success_count += 1

                    # 记录进度
                    if (i + 1) % batch_size == 0:
                        logger.info(f"已插入 {i + 1}/{len(documents)} 个文档")

                except Exception as e:
                    failed_count += 1
                    error_msg = f"文档 {i + 1} 插入失败: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"文档插入完成 | 成功: {success_count} | 失败: {failed_count}"
            )

            return LightRAGInsertResponse(
                total=len(documents),
                success=success_count,
                failed=failed_count,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"批量插入文档失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"文档插入失败: {str(e)}")

    async def cleanup(self) -> None:
        """清理资源"""
        if self.rag:
            try:
                await self.rag.finalize_storages()
                logger.info("LightRAG 资源已释放")
            except Exception as e:
                logger.error(f"释放资源失败: {str(e)}")

    def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引文件统计信息

        Returns
        -------
        Dict[str, Any]
            索引统计信息，包括文件大小、存在性等
        """
        files_info = {}

        index_files = [
            "graph_chunk_entity_relation.graphml",
            "kv_store_doc_status.json",
            "kv_store_full_docs.json",
            "kv_store_text_chunks.json",
            "vdb_chunks.json",
            "vdb_entities.json",
            "vdb_relationships.json",
        ]

        total_size = 0
        for file_name in index_files:
            file_path = os.path.join(self.working_dir, file_name)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                total_size += file_size
                files_info[file_name] = {
                    "exists": True,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / 1024 / 1024, 2),
                }
            else:
                files_info[file_name] = {
                    "exists": False,
                    "size_bytes": 0,
                    "size_mb": 0,
                }

        return {
            "working_dir": self.working_dir,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "files": files_info,
            "initialized": self.initialized,
        }


# 全局服务实例（单例模式）
_lightrag_service: Optional[LightRAGService] = None


def get_lightrag_service() -> LightRAGService:
    """
    获取 LightRAG 服务单例

    Returns
    -------
    LightRAGService
        LightRAG 服务实例
    """
    global _lightrag_service
    if _lightrag_service is None:
        _lightrag_service = LightRAGService(
            working_dir=settings.LIGHTRAG_WORKING_DIR,
            default_mode=settings.LIGHTRAG_RETRIEVAL_MODE,
            default_top_k=settings.LIGHTRAG_TOP_K,
        )
    return _lightrag_service

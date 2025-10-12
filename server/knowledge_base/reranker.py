"""
Reranker模块
支持多种厂商的Reranker API接口调用
"""
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod
from loguru import logger
import httpx


class BaseReranker(ABC):
    """Reranker基类"""

    def __init__(self, api_key: str, top_k: int = 5):
        self.api_key = api_key
        self.top_k = top_k

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """重排序方法"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass


class CohereReranker(BaseReranker):
    """Cohere Rerank API"""

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-multilingual-v3.0",
        top_k: int = 5
    ):
        super().__init__(api_key, top_k)
        self.model = model
        self.api_url = "https://api.cohere.ai/v1/rerank"

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        使用Cohere API进行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        top_k = top_k or self.top_k

        try:
            # 准备文档文本列表
            doc_texts = [doc.get('content', '') for doc in documents]

            # 调用Cohere API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": doc_texts,
                        "top_n": top_k,
                        "return_documents": False
                    }
                )
                response.raise_for_status()
                result = response.json()

            # 处理结果
            reranked_docs = []
            for item in result.get("results", []):
                idx = item["index"]
                score = item["relevance_score"]

                doc = documents[idx].copy()
                doc["rerank_score"] = float(score)
                doc["original_score"] = doc.get("score", 0.0)
                reranked_docs.append(doc)

            logger.info(
                f"Cohere reranked {len(documents)} docs, "
                f"returned top {len(reranked_docs)}"
            )

            return reranked_docs

        except Exception as e:
            logger.error(f"Cohere rerank failed: {e}")
            return documents[:top_k]

    def get_provider_name(self) -> str:
        return "cohere"


class JinaReranker(BaseReranker):
    """Jina AI Reranker API"""

    def __init__(
        self,
        api_key: str,
        model: str = "jina-reranker-v2-base-multilingual",
        top_k: int = 5
    ):
        super().__init__(api_key, top_k)
        self.model = model
        self.api_url = "https://api.jina.ai/v1/rerank"

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        使用Jina AI API进行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        top_k = top_k or self.top_k

        try:
            # 准备文档列表
            doc_texts = [doc.get('content', '') for doc in documents]

            # 调用Jina API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": doc_texts,
                        "top_n": top_k
                    }
                )
                response.raise_for_status()
                result = response.json()

            # 处理结果
            reranked_docs = []
            for item in result.get("results", []):
                idx = item["index"]
                score = item["relevance_score"]

                doc = documents[idx].copy()
                doc["rerank_score"] = float(score)
                doc["original_score"] = doc.get("score", 0.0)
                reranked_docs.append(doc)

            logger.info(
                f"Jina reranked {len(documents)} docs, "
                f"returned top {len(reranked_docs)}"
            )

            return reranked_docs

        except Exception as e:
            logger.error(f"Jina rerank failed: {e}")
            return documents[:top_k]

    def get_provider_name(self) -> str:
        return "jina"


class VoyageReranker(BaseReranker):
    """Voyage AI Reranker API"""

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-lite-1",
        top_k: int = 5
    ):
        super().__init__(api_key, top_k)
        self.model = model
        self.api_url = "https://api.voyageai.com/v1/rerank"

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        使用Voyage AI API进行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        top_k = top_k or self.top_k

        try:
            # 准备文档列表
            doc_texts = [doc.get('content', '') for doc in documents]

            # 调用Voyage API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": doc_texts,
                        "top_k": top_k
                    }
                )
                response.raise_for_status()
                result = response.json()

            # 处理结果
            reranked_docs = []
            for item in result.get("data", []):
                idx = item["index"]
                score = item["relevance_score"]

                doc = documents[idx].copy()
                doc["rerank_score"] = float(score)
                doc["original_score"] = doc.get("score", 0.0)
                reranked_docs.append(doc)

            logger.info(
                f"Voyage reranked {len(documents)} docs, "
                f"returned top {len(reranked_docs)}"
            )

            return reranked_docs

        except Exception as e:
            logger.error(f"Voyage rerank failed: {e}")
            return documents[:top_k]

    def get_provider_name(self) -> str:
        return "voyage"


class BGEReranker(BaseReranker):
    """BGE Reranker API (阿里云/智谱/硅基流动等)"""

    def __init__(
        self,
        api_key: str,
        api_url: str,
        model: str = "bge-reranker-v2-m3",
        top_k: int = 5
    ):
        super().__init__(api_key, top_k)
        self.model = model
        self.api_url = api_url

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        使用BGE Reranker API进行重排序
        支持智谱AI、硅基流动等提供BGE模型的平台

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        top_k = top_k or self.top_k

        try:
            # 准备文档列表
            doc_texts = [doc.get('content', '') for doc in documents]

            # 调用BGE API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": doc_texts,
                        "top_n": top_k
                    }
                )
                response.raise_for_status()
                result = response.json()

            # 处理结果（格式可能因平台而异）
            reranked_docs = []
            results_key = "results" if "results" in result else "data"

            for item in result.get(results_key, []):
                idx = item.get("index", item.get("document_index"))
                score = item.get("relevance_score", item.get("score"))

                doc = documents[idx].copy()
                doc["rerank_score"] = float(score)
                doc["original_score"] = doc.get("score", 0.0)
                reranked_docs.append(doc)

            logger.info(
                f"BGE reranked {len(documents)} docs, "
                f"returned top {len(reranked_docs)}"
            )

            return reranked_docs

        except Exception as e:
            logger.error(f"BGE rerank failed: {e}")
            return documents[:top_k]

    def get_provider_name(self) -> str:
        return "bge"


class Reranker:
    """Reranker统一接口类"""

    def __init__(
        self,
        provider: str = "cohere",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        top_k: int = 5
    ):
        """
        初始化Reranker

        Args:
            provider: 提供商 (cohere, jina, voyage, bge)
            api_key: API密钥
            model: 模型名称
            api_url: API地址（BGE需要）
            top_k: 返回的top结果数量
        """
        self.provider = provider.lower()
        self.top_k = top_k

        # 根据provider创建对应的reranker
        if self.provider == "cohere":
            self.reranker = CohereReranker(
                api_key=api_key,
                model=model or "rerank-multilingual-v3.0",
                top_k=top_k
            )
        elif self.provider == "jina":
            self.reranker = JinaReranker(
                api_key=api_key,
                model=model or "jina-reranker-v2-base-multilingual",
                top_k=top_k
            )
        elif self.provider == "voyage":
            self.reranker = VoyageReranker(
                api_key=api_key,
                model=model or "rerank-lite-1",
                top_k=top_k
            )
        elif self.provider == "bge":
            if not api_url:
                raise ValueError("BGE provider requires api_url")
            self.reranker = BGEReranker(
                api_key=api_key,
                api_url=api_url,
                model=model or "bge-reranker-v2-m3",
                top_k=top_k
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: cohere, jina, voyage, bge"
            )

        logger.info(
            f"Initialized Reranker with provider: {self.provider}, "
            f"top_k: {top_k}"
        )

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回的top结果数量

        Returns:
            重排序后的文档列表
        """
        return await self.reranker.rerank(query, documents, top_k)

    def rerank_with_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        对检索结果进行重排序，返回文档和分数的元组

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回的top结果数量

        Returns:
            (文档, 重排序分数)的元组列表
        """
        import asyncio
        reranked = asyncio.run(self.rerank(query, documents, top_k))
        return [(doc, doc.get('rerank_score', 0.0)) for doc in reranked]

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.provider,
            "provider_name": self.reranker.get_provider_name(),
            "top_k": self.top_k,
            "available": True
        }

"""Knowledge base service implemented with LangChain primitives."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from gustobot.config import settings
from .embeddings import OpenAICompatibleEmbeddings
from .vector_store import VectorStore
from .reranker import Reranker


class KnowledgeService:
    """Facade for ingesting documents and performing similarity search."""

    def __init__(
        self,
        *,
        vector_store: Optional[VectorStore] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        self.chunk_size = chunk_size or settings.KB_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.KB_CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", " "],
            length_function=len,  # 使用字符长度而不是 tiktoken
        )

        embedding_api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        self.embedder = OpenAICompatibleEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=embedding_api_key,
            base_url=settings.EMBEDDING_BASE_URL,
            dimension=settings.EMBEDDING_DIMENSION,
        )

        self.vector_store = vector_store or VectorStore(
            collection_name=settings.MILVUS_COLLECTION,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            dimension=settings.EMBEDDING_DIMENSION,
            index_type=settings.MILVUS_INDEX_TYPE,
            metric_type=settings.MILVUS_METRIC_TYPE,
        )

        self.reranker = Reranker()

        logger.info(
            "KnowledgeService initialised (chunk_size=%s, chunk_overlap=%s)",
            self.chunk_size,
            self.chunk_overlap,
        )

    async def ingest_text(
        self,
        text: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"add_count": 0, "ids": []}

        documents = await asyncio.to_thread(self._split_into_documents, text, metadata or {})
        if not documents:
            return {"add_count": 0, "ids": []}

        embeddings = await asyncio.to_thread(
            self.embedder.embed_documents,
            [doc.page_content for doc in documents],
        )

        result = await asyncio.to_thread(self._store_documents, documents, embeddings)
        return result

    async def add_document(
        self,
        *,
        doc_id: Optional[str],
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        meta = metadata.copy() if metadata else {}
        meta.setdefault("title", title)
        meta.setdefault("name", title)
        if doc_id:
            meta.setdefault("recipe_id", doc_id)
        result = await self.ingest_text(content, metadata=meta)
        return result.get("add_count", 0) > 0

    async def add_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> bool:
        document = self._format_recipe_document(recipe_data)
        metadata = {
            "recipe_id": recipe_id,
            "name": recipe_data.get("name", ""),
            "category": recipe_data.get("category", ""),
            "difficulty": recipe_data.get("difficulty", ""),
        }
        result = await self.ingest_text(document, metadata=metadata)
        return result.get("add_count", 0) > 0

    async def add_recipes_batch(self, recipes: List[Dict[str, Any]]) -> Dict[str, int]:
        success_count = 0
        error_count = 0
        for recipe in recipes:
            recipe_id = recipe.get("id") or recipe.get("recipe_id") or str(uuid4())
            if await self.add_recipe(recipe_id, recipe):
                success_count += 1
            else:
                error_count += 1
        return {"success": success_count, "error": error_count, "total": len(recipes)}

    async def search(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        top_k = top_k or settings.KB_TOP_K
        similarity_threshold = (
            similarity_threshold if similarity_threshold is not None else settings.KB_SIMILARITY_THRESHOLD
        )

        # 如果启用 reranker，先召回更多候选文档
        recall_k = top_k
        if self.reranker.enabled:
            recall_k = settings.RERANK_MAX_CANDIDATES  # 召回更多文档用于重排

        embedding = await asyncio.to_thread(self.embedder.embed_query, query)
        results = await asyncio.to_thread(
            self.vector_store.search,
            embedding,
            recall_k,  # 使用更大的召回数量
            filter_expr,
        )

        filtered = [r for r in results if r.get("score", 0.0) >= similarity_threshold]

        # 使用 reranker 精排
        if filtered and self.reranker.enabled:
            filtered = await self.reranker.rerank(query, filtered, top_k)

        return filtered[:top_k]

    async def delete_recipe(self, recipe_id: str) -> bool:
        return await asyncio.to_thread(self.vector_store.delete_documents, [recipe_id])

    async def get_stats(self) -> Dict[str, Any]:
        def _stats() -> Dict[str, Any]:
            stats = self.vector_store.get_collection_stats()
            stats.update(
                {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "embedding_model": settings.EMBEDDING_MODEL,
                }
            )
            return stats

        return await asyncio.to_thread(_stats)

    async def clear(self) -> bool:
        return await asyncio.to_thread(self.vector_store.clear_collection)

    async def close(self) -> None:
        await asyncio.to_thread(self.vector_store.close)

    def _split_into_documents(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        base_document = Document(page_content=text, metadata=metadata)
        chunks = self.splitter.split_documents([base_document])
        return chunks or [base_document]

    def _store_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]],
    ) -> Dict[str, Any]:
        if not documents or not embeddings:
            return {"add_count": 0, "ids": [], "stored": False}

        ids: List[str] = []
        contents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for index, doc in enumerate(documents):
            metadata = dict(doc.metadata or {})
            base_id = metadata.get("recipe_id") or metadata.get("id") or metadata.get("source") or uuid4().hex
            chunk_id = f"{base_id}_{index}"
            metadata.setdefault("recipe_id", base_id)
            metadata.setdefault("chunk_id", chunk_id)
            metadata.setdefault("name", metadata.get("name") or metadata.get("title") or "")

            ids.append(chunk_id)
            contents.append(doc.page_content)
            metadatas.append(metadata)

        success = self.vector_store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )

        return {"add_count": len(ids) if success else 0, "ids": ids, "stored": success}

    def _format_recipe_document(self, recipe: Dict[str, Any]) -> str:
        parts: List[str] = []
        name = recipe.get("name")
        if name:
            parts.append(f"菜名：{name}")

        category = recipe.get("category")
        if category:
            parts.append(f"分类：{category}")

        difficulty = recipe.get("difficulty")
        if difficulty:
            parts.append(f"难度：{difficulty}")

        time_cost = recipe.get("time") or recipe.get("cook_time")
        if time_cost:
            parts.append(f"耗时：{time_cost}")

        ingredients = recipe.get("ingredients") or recipe.get("ingredient_list")
        if ingredients:
            if isinstance(ingredients, list):
                formatted = "、".join(str(item) for item in ingredients)
            else:
                formatted = str(ingredients)
            parts.append(f"食材：{formatted}")

        steps = recipe.get("steps")
        if steps:
            if isinstance(steps, list):
                step_lines = [f"步骤{idx + 1}：{step}" for idx, step in enumerate(steps)]
                parts.extend(step_lines)
            else:
                parts.append(f"步骤：{steps}")

        tips = recipe.get("tips")
        if tips:
            parts.append(f"小贴士：{tips}")

        nutrition = recipe.get("nutrition")
        if nutrition:
            if isinstance(nutrition, dict):
                nutritions = [f"{k}: {v}" for k, v in nutrition.items()]
                parts.append("营养：" + "、".join(nutritions))
            else:
                parts.append(f"营养：{nutrition}")

        return "\n".join(parts)

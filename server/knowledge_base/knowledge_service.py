"""
知识库服务
提供高级知识库操作接口，整合Milvus、OpenAI Embedding和Reranker
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from .vector_store import VectorStore
from .embedding_service import EmbeddingService
from .reranker import Reranker
from server.config import settings


class KnowledgeService:
    """知识库服务类"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        reranker: Optional[Reranker] = None
    ):
        """
        初始化知识库服务

        Args:
            vector_store: 向量数据库实例
            embedding_service: Embedding服务实例
            reranker: Reranker实例
        """
        # 初始化Embedding服务
        if embedding_service is None:
            embedding_service = EmbeddingService(
                api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL,
                dimensions=settings.EMBEDDING_DIMENSION
            )
        self.embedding_service = embedding_service

        # 初始化向量存储
        if vector_store is None:
            vector_store = VectorStore(
                collection_name=settings.MILVUS_COLLECTION,
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                dimension=settings.EMBEDDING_DIMENSION,
                index_type=settings.MILVUS_INDEX_TYPE,
                metric_type=settings.MILVUS_METRIC_TYPE
            )
        self.vector_store = vector_store

        # 初始化Reranker (API-based)
        if reranker is None:
            reranker = Reranker(
                provider=settings.RERANKER_PROVIDER,
                api_key=settings.RERANKER_API_KEY,
                model=settings.RERANKER_MODEL,
                api_url=settings.RERANKER_API_URL,
                top_k=settings.RERANKER_TOP_K
            )
        self.reranker = reranker

        logger.info("KnowledgeService initialized with Milvus + OpenAI Embedding + Reranker")

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        use_reranker: bool = True,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库

        Args:
            query: 查询文本
            top_k: 最终返回结果数量
            similarity_threshold: 相似度阈值
            use_reranker: 是否使用重排序
            filter_expr: Milvus过滤表达式

        Returns:
            搜索结果列表
        """
        if top_k is None:
            top_k = settings.KB_TOP_K

        if similarity_threshold is None:
            similarity_threshold = settings.KB_SIMILARITY_THRESHOLD

        try:
            # 1. 生成查询向量
            logger.debug("Generating query embedding")
            query_embedding = await self.embedding_service.embed_query(query)

            # 2. 向量检索 - 召回更多候选结果用于重排序
            recall_size = top_k * 3 if use_reranker else top_k
            logger.debug(f"Searching Milvus with recall_size={recall_size}")

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=recall_size,
                filter_expr=filter_expr
            )

            if not results:
                logger.info("No results found in vector search")
                return []

            # 3. 过滤低相似度结果
            filtered_results = [
                r for r in results
                if r.get("score", 0) >= similarity_threshold
            ]

            logger.info(
                f"Vector search: {len(results)} found, "
                f"{len(filtered_results)} after similarity filtering"
            )

            # 4. 重排序
            if use_reranker and filtered_results:
                logger.debug("Applying reranker")
                reranked_results = await self.reranker.rerank(
                    query=query,
                    documents=filtered_results,
                    top_k=top_k
                )
                final_results = reranked_results
            else:
                final_results = filtered_results[:top_k]

            logger.info(f"Final results: {len(final_results)} documents")

            return final_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def add_recipe(
        self,
        recipe_id: str,
        recipe_data: Dict[str, Any]
    ) -> bool:
        """
        添加菜谱到知识库

        Args:
            recipe_id: 菜谱ID
            recipe_data: 菜谱数据

        Returns:
            是否成功
        """
        try:
            # 1. 构建文档文本
            document = self._format_recipe_document(recipe_data)

            # 2. 生成embedding
            logger.debug(f"Generating embedding for recipe: {recipe_id}")
            embedding = await self.embedding_service.embed_text(document)

            # 3. 构建元数据
            metadata = {
                "recipe_id": recipe_id,
                "name": recipe_data.get("name", ""),
                "category": recipe_data.get("category", ""),
                "difficulty": recipe_data.get("difficulty", ""),
            }

            # 4. 添加到向量数据库
            success = self.vector_store.add_documents(
                ids=[recipe_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata]
            )

            if success:
                logger.info(f"Added recipe: {recipe_id}")
            else:
                logger.error(f"Failed to add recipe: {recipe_id}")

            return success

        except Exception as e:
            logger.error(f"Error adding recipe {recipe_id}: {e}")
            return False

    async def add_recipes_batch(
        self,
        recipes: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        批量添加菜谱

        Args:
            recipes: 菜谱列表

        Returns:
            统计信息 {"success": count, "failed": count}
        """
        documents = []
        metadatas = []
        ids = []

        # 准备数据
        for recipe in recipes:
            recipe_id = recipe.get("id") or recipe.get("recipe_id")
            if not recipe_id:
                logger.warning("Recipe missing ID, skipping")
                continue

            document = self._format_recipe_document(recipe)
            metadata = {
                "recipe_id": recipe_id,
                "name": recipe.get("name", ""),
                "category": recipe.get("category", ""),
                "difficulty": recipe.get("difficulty", ""),
            }

            documents.append(document)
            metadatas.append(metadata)
            ids.append(str(recipe_id))

        try:
            # 批量生成embeddings
            logger.info(f"Generating embeddings for {len(documents)} recipes")
            embeddings = await self.embedding_service.embed_texts(documents)

            # 批量添加到向量数据库
            logger.info(f"Adding {len(ids)} recipes to Milvus")
            success = self.vector_store.add_documents(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            result = {
                "success": len(documents) if success else 0,
                "failed": 0 if success else len(documents)
            }

            logger.info(f"Batch add completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            return {
                "success": 0,
                "failed": len(documents)
            }

    def _format_recipe_document(self, recipe: Dict[str, Any]) -> str:
        """
        将菜谱数据格式化为文档文本

        Args:
            recipe: 菜谱数据

        Returns:
            格式化的文档文本
        """
        parts = []

        # 基本信息
        if "name" in recipe:
            parts.append(f"菜名：{recipe['name']}")

        if "category" in recipe:
            parts.append(f"分类：{recipe['category']}")

        if "difficulty" in recipe:
            parts.append(f"难度：{recipe['difficulty']}")

        if "time" in recipe:
            parts.append(f"耗时：{recipe['time']}")

        # 食材
        if "ingredients" in recipe:
            ingredients_text = "食材：" + "、".join(recipe["ingredients"])
            parts.append(ingredients_text)

        # 步骤
        if "steps" in recipe:
            steps_text = "步骤：\n" + "\n".join([
                f"{i+1}. {step}" for i, step in enumerate(recipe["steps"])
            ])
            parts.append(steps_text)

        # 技巧
        if "tips" in recipe:
            tips_text = "小贴士：" + recipe["tips"]
            parts.append(tips_text)

        # 营养信息
        if "nutrition" in recipe:
            nutrition = recipe["nutrition"]
            nutrition_text = f"营养：热量{nutrition.get('calories', 'N/A')}千卡"
            parts.append(nutrition_text)

        return "\n\n".join(parts)

    async def delete_recipe(self, recipe_id: str) -> bool:
        """
        删除菜谱

        Args:
            recipe_id: 菜谱ID

        Returns:
            是否成功
        """
        success = self.vector_store.delete_documents([recipe_id])
        if success:
            logger.info(f"Deleted recipe: {recipe_id}")
        return success

    async def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = self.vector_store.get_collection_stats()
        stats["embedding_model"] = self.embedding_service.get_model_name()
        stats["embedding_dimension"] = self.embedding_service.get_dimension()
        stats["reranker_model"] = self.reranker.get_model_info()
        return stats

    async def clear(self) -> bool:
        """清空知识库"""
        logger.warning("Clearing knowledge base")
        return self.vector_store.clear_collection()

    def close(self):
        """关闭所有连接"""
        self.vector_store.close()
        logger.info("Knowledge service closed")

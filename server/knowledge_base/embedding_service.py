"""
OpenAI Embedding服务
使用OpenAI API生成文本嵌入向量
"""
from typing import List, Optional
from loguru import logger
from openai import AsyncOpenAI
from server.config import settings


class EmbeddingService:
    """OpenAI Embedding服务类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536
    ):
        """
        初始化Embedding服务

        Args:
            api_key: OpenAI API密钥
            model: 嵌入模型名称
            dimensions: 向量维度
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.dimensions = dimensions
        self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info(f"Initialized EmbeddingService with model: {self.model}")

    async def embed_text(self, text: str) -> List[float]:
        """
        为单个文本生成嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        try:
            # OpenAI API支持批量处理，但有数量限制
            # 这里分批处理，每批最多2048个
            batch_size = 2048
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated embeddings for batch {i//batch_size + 1}")

            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        为查询文本生成嵌入向量
        （某些模型对query和document有不同的处理，这里保持一致）

        Args:
            query: 查询文本

        Returns:
            嵌入向量
        """
        return await self.embed_text(query)

    def get_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.dimensions

    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model

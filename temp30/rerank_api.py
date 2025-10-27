from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import openai
import numpy as np
from dataclasses import dataclass

app = FastAPI(title="Rerank API Service")

# ============ 配置 ============
PGVECTOR_CONFIG = {
    "host": "localhost",
    "database": "vector_db",
    "user": "postgres",
    "password": "password"
}

OPENAI_API_KEY = "your-api-key"
EMBEDDING_MODEL = "text-embedding-3-small"
RERANK_MODEL = "gpt-4o-mini"  # 用于 rerank 的模型


# ============ 数据模型 ============
class RerankRequest(BaseModel):
    query: str = Field(..., description="用户查询问题")
    top_k: int = Field(default=10, description="初次召回数量")
    rerank_top_k: int = Field(default=5, description="Rerank 后返回数量")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    use_rerank: bool = Field(default=True, description="是否启用 Rerank")


class DocumentResult(BaseModel):
    document_id: int
    chunk_index: int
    content: str
    score: float
    metadata: Optional[Dict] = None


class RerankResponse(BaseModel):
    query: str
    results: List[DocumentResult]
    total_retrieved: int
    reranked: bool


# ============ 核心服务 ============
class EmbeddingService:
    """处理 Embedding 生成"""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """生成文本向量"""
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding


class VectorSearchService:
    """向量检索服务"""

    def __init__(self):
        self.conn = psycopg2.connect(**PGVECTOR_CONFIG)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        向量相似度检索
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # 构建 SQL 查询
        query = """
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                metadata,
                1 - (embedding <=> %s::vector) as score
            FROM document_embeddings
        """

        params = [query_embedding]

        # 添加过滤条件
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"metadata->>'{key}' = %s")
                params.append(str(value))
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, top_k])

        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()

        return [dict(row) for row in results]

    def close(self):
        self.conn.close()


class RerankService:
    """Rerank 服务"""

    @staticmethod
    def rerank_with_llm(query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """
        使用 LLM 进行 Rerank
        方法：让 LLM 评分每个文档与查询的相关性
        """
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        # 构建 prompt
        docs_text = "\n\n".join([
            f"[{i}] {doc['content'][:500]}"  # 限制长度
            for i, doc in enumerate(documents)
        ])

        prompt = f"""Given the query and documents below, score each document's relevance to the query on a scale of 0-100.
Return ONLY a JSON array of scores in order, like: [85, 92, 45, ...]

Query: {query}

Documents:
{docs_text}

Scores (JSON array only):"""

        try:
            response = client.chat.completions.create(
                model=RERANK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            # 解析评分
            import json
            scores = json.loads(response.choices[0].message.content.strip())

            # 将评分归一化到 0-1
            scores = [s / 100.0 for s in scores]

            # 为文档添加 rerank 分数
            for doc, score in zip(documents, scores):
                doc['rerank_score'] = score

            # 按 rerank 分数排序并返回 top_k
            documents.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            return documents[:top_k]

        except Exception as e:
            print(f"Rerank error: {e}")
            # 失败时返回原始排序
            return documents[:top_k]

    @staticmethod
    def rerank_with_cross_encoder(query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """
        使用 Cross-Encoder 模型进行 Rerank（可选方案）
        需要安装: pip install sentence-transformers
        """
        try:
            from sentence_transformers import CrossEncoder

            model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

            # 准备 query-document 对
            pairs = [[query, doc['content']] for doc in documents]

            # 计算分数
            scores = model.predict(pairs)

            # 添加 rerank 分数
            for doc, score in zip(documents, scores):
                doc['rerank_score'] = float(score)

            # 排序并返回
            documents.sort(key=lambda x: x['rerank_score'], reverse=True)
            return documents[:top_k]

        except ImportError:
            print("Cross-encoder not available, falling back to LLM rerank")
            return RerankService.rerank_with_llm(query, documents, top_k)


# ============ API 端点 ============
@app.post("/rerank", response_model=RerankResponse)
async def rerank_endpoint(request: RerankRequest):
    """
    Rerank API 主入口

    流程：
    1. 将查询转换为向量
    2. 在 pgvector 中检索 top_k 个最相关文档
    3. (可选) 使用 Rerank 模型重新排序
    4. 返回最终结果
    """
    try:
        # Step 1: 生成查询向量
        query_embedding = EmbeddingService.get_embedding(request.query)

        # Step 2: 向量检索
        vector_service = VectorSearchService()
        initial_results = vector_service.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=request.filters
        )
        vector_service.close()

        if not initial_results:
            return RerankResponse(
                query=request.query,
                results=[],
                total_retrieved=0,
                reranked=False
            )

        # Step 3: Rerank
        if request.use_rerank and len(initial_results) > request.rerank_top_k:
            reranked_results = RerankService.rerank_with_llm(
                query=request.query,
                documents=initial_results,
                top_k=request.rerank_top_k
            )
            final_results = reranked_results
            reranked = True
        else:
            final_results = initial_results[:request.rerank_top_k]
            reranked = False

        # Step 4: 格式化返回结果
        results = [
            DocumentResult(
                document_id=doc['document_id'],
                chunk_index=doc['chunk_index'],
                content=doc['content'],
                score=doc.get('rerank_score', doc.get('score', 0)),
                metadata=doc.get('metadata')
            )
            for doc in final_results
        ]

        return RerankResponse(
            query=request.query,
            results=results,
            total_retrieved=len(initial_results),
            reranked=reranked
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed")
async def embed_document(
    document_id: int,
    content: str,
    metadata: Optional[Dict] = None
):
    """
    将文档内容向量化并存入 pgvector
    """
    try:
        # 生成向量
        embedding = EmbeddingService.get_embedding(content)

        # 存储到 pgvector
        conn = psycopg2.connect(**PGVECTOR_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO document_embeddings
            (document_id, chunk_index, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            document_id,
            0,
            content,
            embedding,
            psycopg2.extras.Json(metadata or {})
        ))

        embedding_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "embedding_id": embedding_id,
            "document_id": document_id,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

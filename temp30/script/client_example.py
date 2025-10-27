"""
Rerank API 客户端调用示例
"""
import requests
from typing import List, Dict, Optional


class RerankClient:
    """Rerank API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def rerank(
        self,
        query: str,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: Optional[Dict] = None,
        use_rerank: bool = True
    ) -> Dict:
        """
        调用 Rerank API

        Args:
            query: 用户查询
            top_k: 初次向量检索召回数量
            rerank_top_k: Rerank 后返回数量
            filters: 过滤条件，如 {"category": "技术文档"}
            use_rerank: 是否启用 Rerank

        Returns:
            API 响应结果
        """
        response = requests.post(
            f"{self.base_url}/rerank",
            json={
                "query": query,
                "top_k": top_k,
                "rerank_top_k": rerank_top_k,
                "filters": filters,
                "use_rerank": use_rerank
            }
        )
        response.raise_for_status()
        return response.json()

    def embed_document(
        self,
        document_id: int,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        将文档向量化并存储

        Args:
            document_id: 文档 ID（关联 MySQL）
            content: 文档内容
            metadata: 元数据

        Returns:
            存储结果
        """
        response = requests.post(
            f"{self.base_url}/embed",
            params={"document_id": document_id},
            json={
                "content": content,
                "metadata": metadata
            }
        )
        response.raise_for_status()
        return response.json()


# ============ 使用示例 ============
if __name__ == "__main__":
    client = RerankClient()

    # 示例 1: 存储文档向量
    print("=" * 50)
    print("示例 1: 存储文档向量")
    print("=" * 50)

    result = client.embed_document(
        document_id=12345,
        content="FastAPI 是一个现代化的 Python Web 框架，支持异步编程和自动 API 文档生成。",
        metadata={
            "title": "FastAPI 介绍",
            "category": "技术文档",
            "author": "张三"
        }
    )
    print(f"存储结果: {result}")

    # 示例 2: 基础检索（不使用 Rerank）
    print("\n" + "=" * 50)
    print("示例 2: 基础向量检索（无 Rerank）")
    print("=" * 50)

    results = client.rerank(
        query="如何使用 Python 构建 Web API？",
        top_k=10,
        rerank_top_k=5,
        use_rerank=False  # 不使用 Rerank
    )

    print(f"查询: {results['query']}")
    print(f"召回数量: {results['total_retrieved']}")
    print(f"是否 Rerank: {results['reranked']}")
    print(f"\n前 {len(results['results'])} 个结果:")
    for i, doc in enumerate(results['results'], 1):
        print(f"\n[{i}] 文档 ID: {doc['document_id']}")
        print(f"    分数: {doc['score']:.4f}")
        print(f"    内容: {doc['content'][:100]}...")
        if doc.get('metadata'):
            print(f"    元数据: {doc['metadata']}")

    # 示例 3: 使用 Rerank
    print("\n" + "=" * 50)
    print("示例 3: 向量检索 + LLM Rerank")
    print("=" * 50)

    results = client.rerank(
        query="如何使用 Python 构建 Web API？",
        top_k=20,         # 初次召回 20 个
        rerank_top_k=5,   # Rerank 后返回 5 个
        use_rerank=True   # 启用 Rerank
    )

    print(f"查询: {results['query']}")
    print(f"初次召回: {results['total_retrieved']} 个")
    print(f"是否 Rerank: {results['reranked']}")
    print(f"最终返回: {len(results['results'])} 个")
    print(f"\nRerank 后的 Top {len(results['results'])} 结果:")
    for i, doc in enumerate(results['results'], 1):
        print(f"\n[{i}] 文档 ID: {doc['document_id']}")
        print(f"    Rerank 分数: {doc['score']:.4f}")
        print(f"    内容: {doc['content'][:100]}...")

    # 示例 4: 带过滤条件的检索
    print("\n" + "=" * 50)
    print("示例 4: 带过滤条件的检索")
    print("=" * 50)

    results = client.rerank(
        query="API 开发教程",
        top_k=10,
        rerank_top_k=3,
        filters={"category": "技术文档"},  # 只检索技术文档分类
        use_rerank=True
    )

    print(f"查询: {results['query']}")
    print(f"过滤条件: category=技术文档")
    print(f"结果数量: {len(results['results'])}")

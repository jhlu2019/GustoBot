"""测试 LLM、Reranker 和 Embedding 服务是否可用"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_llm():
    """测试 LLM 服务"""
    print("\n" + "="*50)
    print("测试 LLM 服务")
    print("="*50)

    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    print(f"Base URL: {base_url}")
    print(f"Model: {model}")

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "你好，请用一句话介绍你自己"}
                ],
                "temperature": 0.3,
                "max_tokens": 100
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ LLM 服务正常")
            print(f"响应: {content}")
            return True
        else:
            print(f"❌ LLM 服务异常")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ LLM 服务连接失败: {e}")
        return False


def test_reranker():
    """测试 Reranker 服务"""
    print("\n" + "="*50)
    print("测试 Reranker 服务")
    print("="*50)

    enabled = os.getenv("RERANK_ENABLED", "false").lower() == "true"
    print(f"Reranker 是否启用: {enabled}")

    if not enabled:
        print("⚠️  Reranker 未启用 (RERANK_ENABLED=false)")
        return None

    base_url = os.getenv("RERANK_BASE_URL")
    endpoint = os.getenv("RERANK_ENDPOINT")
    api_key = os.getenv("RERANK_API_KEY")
    model = os.getenv("RERANK_MODEL")

    url = f"{base_url}{endpoint}"
    print(f"URL: {url}")
    print(f"Model: {model}")

    try:
        # 测试数据
        test_query = "如何申请高新技术企业认定？"
        test_documents = [
            "高新技术企业认定需要满足以下条件：企业拥有核心自主知识产权",
            "企业招聘信息：诚聘软件工程师，要求本科以上学历",
            "科技部关于高新技术企业认定管理办法的通知"
        ]

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "query": test_query,
                "documents": test_documents,
                "top_n": 3
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Reranker 服务正常")
            print(f"响应示例:")
            if 'results' in result:
                for i, item in enumerate(result['results'][:3]):
                    print(f"  [{i+1}] Score: {item.get('relevance_score', 'N/A'):.4f}")
                    print(f"      Text: {item.get('document', {}).get('text', '')[:50]}...")
            else:
                print(f"  {result}")
            return True
        else:
            print(f"❌ Reranker 服务异常")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Reranker 服务连接失败: {e}")
        return False


def test_embedding():
    """测试 Embedding 服务"""
    print("\n" + "="*50)
    print("测试 Embedding 服务")
    print("="*50)

    base_url = os.getenv("EMBEDDING_BASE_URL")
    api_key = os.getenv("EMBEDDING_API_KEY")
    model = os.getenv("EMBEDDING_MODEL")
    dimension = os.getenv("EMBEDDING_DIMENSION", "1024")

    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print(f"Dimension: {dimension}")

    try:
        response = requests.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": "这是一个测试文本"
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            embedding = result['data'][0]['embedding']
            print(f"✅ Embedding 服务正常")
            print(f"向量维度: {len(embedding)}")
            print(f"向量示例 (前5维): {embedding[:5]}")
            return True
        else:
            print(f"❌ Embedding 服务异常")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Embedding 服务连接失败: {e}")
        return False


def main():
    """主函数"""
    print("\n🔍 开始测试所有服务...")

    results = {
        "LLM": test_llm(),
        "Embedding": test_embedding(),
        "Reranker": test_reranker()
    }

    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    for service, result in results.items():
        if result is True:
            status = "✅ 正常"
        elif result is False:
            status = "❌ 异常"
        else:
            status = "⚠️  未启用"
        print(f"{service:12s}: {status}")

    print("\n✨ 测试完成！")


if __name__ == "__main__":
    main()

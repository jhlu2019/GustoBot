"""单独测试 Reranker 服务"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 临时启用 reranker 进行测试
base_url = os.getenv("RERANK_BASE_URL", "http://10.168.2.110:9997")
endpoint = os.getenv("RERANK_ENDPOINT", "/rerank")
api_key = os.getenv("RERANK_API_KEY", "sk-72tkvudyGLPMi")
model = os.getenv("RERANK_MODEL", "bge-reranker-large")

url = f"{base_url}{endpoint}"

print("="*50)
print("测试 Reranker 服务")
print("="*50)
print(f"URL: {url}")
print(f"Model: {model}")
print()

# 测试数据
test_query = "如何申请高新技术企业认定？"
test_documents = [
    "高新技术企业认定需要满足以下条件：企业拥有核心自主知识产权",
    "企业招聘信息：诚聘软件工程师，要求本科以上学历",
    "科技部关于高新技术企业认定管理办法的通知",
    "常州市促进知识产权高质量发展的若干政策",
    "企业年度报告显示营收增长20%"
]

print(f"查询: {test_query}")
print(f"候选文档数: {len(test_documents)}")
print()

try:
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
            "top_n": 5
        },
        timeout=30
    )

    print(f"HTTP 状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        print("✅ Reranker 服务正常")
        print()
        print("重排序结果:")
        print("-" * 50)

        if 'results' in result:
            for i, item in enumerate(result['results']):
                score = item.get('relevance_score', 0)
                index = item.get('index', i)
                text = test_documents[index] if index < len(test_documents) else "N/A"
                print(f"[{i+1}] Score: {score:.4f}")
                print(f"    Index: {index}")
                print(f"    Text: {text}")
                print()
        else:
            print("完整响应:")
            print(result)
    else:
        print(f"❌ Reranker 服务异常")
        print(f"响应: {response.text}")

except Exception as e:
    print(f"❌ 连接失败: {e}")
    import traceback
    traceback.print_exc()

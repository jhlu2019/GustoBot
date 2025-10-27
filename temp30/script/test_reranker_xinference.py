"""测试 Xinference Reranker 服务"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

base_url = "http://10.168.2.110:9997/v1"
api_key = "sk-72tkvudyGLPMi"
model = "bge-reranker-large"

print("="*50)
print("测试 Xinference Reranker 服务")
print("="*50)
print(f"Base URL: {base_url}")
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

# 尝试不同的 API 格式

# 格式1: /v1/rerank (标准格式)
print("尝试格式1: /v1/rerank")
print("-" * 50)
try:
    response = requests.post(
        f"{base_url}/rerank",
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

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✅ 成功!")
        result = response.json()
        print("\n重排序结果:")
        if 'results' in result:
            for i, item in enumerate(result['results'][:3]):
                print(f"  [{i+1}] Score: {item.get('relevance_score', 0):.4f}")
                print(f"      Index: {item.get('index', i)}")
                print(f"      Text: {test_documents[item.get('index', i)][:50]}...")
    else:
        print(f"失败: {response.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

print("\n")

# 格式2: Cohere 兼容格式
print("尝试格式2: Cohere 兼容格式")
print("-" * 50)
try:
    response = requests.post(
        f"{base_url}/rerank",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "query": test_query,
            "documents": test_documents,
            "return_documents": True
        },
        timeout=30
    )

    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✅ 成功!")
        result = response.json()
        print("\n重排序结果:")
        if 'results' in result:
            for i, item in enumerate(result['results'][:3]):
                print(f"  [{i+1}] Score: {item.get('relevance_score', 0):.4f}")
                print(f"      Index: {item.get('index', i)}")
        elif isinstance(result, list):
            for i, item in enumerate(result[:3]):
                print(f"  [{i+1}] {item}")
        else:
            print(f"  响应: {result}")
    else:
        print(f"失败: {response.text[:200]}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "="*50)
print("测试完成")
print("="*50)

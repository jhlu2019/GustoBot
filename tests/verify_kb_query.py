#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证kb-query功能"""

import requests
import json

# 1. 验证知识库搜索API
print("=" * 60)
print("1. 测试知识库搜索API")
print("=" * 60)

search_response = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    headers={"Content-Type": "application/json"},
    json={
        "query": "东坡肉",
        "top_k": 5
    }
)

print(f"Status: {search_response.status_code}")
if search_response.status_code == 200:
    results = search_response.json().get('results', [])
    print(f"Found {len(results)} results in Milvus")
    for i, r in enumerate(results[:3]):
        name = r.get('metadata', {}).get('name', 'N/A')
        score = r.get('score', 0)
        print(f"\nResult {i+1}:")
        print(f"  Name: {name}")
        print(f"  Score: {score:.3f}")
        print(f"  Content: {r.get('content', '')[:100]}...")

# 2. 测试kb-query路由
print("\n" + "=" * 60)
print("2. 测试kb-query路由")
print("=" * 60)

test_questions = [
    "东坡肉的历史",
    "麻婆豆腐的来历",
    "佛跳墙的典故",
    "宫保鸡丁是谁发明的"
]

for i, question in enumerate(test_questions, 1):
    print(f"\nTest {i}: {question}")
    print("-" * 40)

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={
            "message": question,
            "session_id": f"verify_kb_{i}"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Route: {result.get('route', 'N/A')}")

        # 检查路由类型
        if result.get('route') == 'kb-query':
            print("✓ Successfully routed to kb-query")
        elif result.get('route') == 'graphrag-query':
            print("ⓘ Routed to graphrag-query (Neo4j)")

        # 检查回答
        answer = result.get('message', '')
        if '暂未找到' in answer:
            print("⚠ No data found")
        else:
            print(f"✓ Got answer (length: {len(answer)})")
            print(f"Preview: {answer[:100]}...")

        # 检查数据源
        if result.get('sources'):
            print(f"✓ Sources: {len(result['sources'])} items")
    else:
        print(f"✗ Error: {response.status_code}")

# 3. 在backend容器中检查数据统计
print("\n" + "=" * 60)
print("3. 数据统计验证")
print("=" * 60)

import subprocess

# 检查Milvus
print("\nMilvus Collection Stats:")
try:
    stats_cmd = """docker exec gustobot-backend-1 python -c "
from gustobot.infrastructure.knowledge.vector_store import VectorStore
store = VectorStore()
stats = store.get_stats()
print(f'Collection: {store.collection_name}')
print(f'Document count: {stats.get(\"document_count\", \"Unknown\")}')
print(f'Index status: {stats.get(\"index_status\", \"Unknown\")}')
"
"""
    result = subprocess.run(stats_cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
except:
    print("Could not get Milvus stats")

# 检查PostgreSQL
print("\nPostgreSQL Tables:")
try:
    pg_cmd = "docker exec gustobot-kb_postgres-1 psql -U postgres -d vector_db -c \"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%historical%';\""
    result = subprocess.run(pg_cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
except:
    print("Could not get PostgreSQL tables")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
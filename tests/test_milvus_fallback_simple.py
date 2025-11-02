#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单测试Milvus fallback机制"""

import requests

print("=" * 60)
print("测试PostgreSQL → Milvus Fallback机制")
print("=" * 60)

# 测试1: 红烧肉历史渊源（PostgreSQL应该有）
print("\n1. 测试PostgreSQL中已有的数据:")
print("   查询: 红烧肉的历史渊源")

pg_data = {
    "query": "红烧肉的历史渊源",
    "top_k": 3,
    "pg_only": True
}

milvus_data = {
    "query": "红烧肉的历史渊源",
    "top_k": 3,
    "vector_only": True
}

# 查PostgreSQL
try:
    resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=pg_data, timeout=10)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"   PostgreSQL结果: {len(results)} 条")
    else:
        print(f"   PostgreSQL查询失败: {resp.status_code}")
except Exception as e:
    print(f"   PostgreSQL错误: {e}")

# 查Milvus
try:
    resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=milvus_data, timeout=10)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"   Milvus结果: {len(results)} 条")
    else:
        print(f"   Milvus查询失败: {resp.status_code}")
except Exception as e:
    print(f"   Milvus错误: {e}")

# 测试2: 北京烤鸭（PostgreSQL可能没有）
print("\n2. 测试PostgreSQL中可能没有的数据:")
print("   查询: 北京烤鸭的制作工艺")

pg_data2 = {
    "query": "北京烤鸭的制作工艺",
    "top_k": 3,
    "pg_only": True
}

milvus_data2 = {
    "query": "北京烤鸭的制作工艺",
    "top_k": 3,
    "vector_only": True
}

# 查PostgreSQL
try:
    resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=pg_data2, timeout=10)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"   PostgreSQL结果: {len(results)} 条")
    else:
        print(f"   PostgreSQL查询失败: {resp.status_code}")
except Exception as e:
    print(f"   PostgreSQL错误: {e}")

# 查Milvus
try:
    resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=milvus_data2, timeout=10)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"   Milvus结果: {len(results)} 条")
        if results:
            for i, r in enumerate(results[:2], 1):
                name = r.get("metadata", {}).get("菜品名称", "N/A")
                print(f"     {i}. {name} (score: {r.get('score', 0):.3f})")
    else:
        print(f"   Milvus查询失败: {resp.status_code}")
except Exception as e:
    print(f"   Milvus错误: {e}")

# 测试3: 通过chat API测试路由
print("\n3. 通过Chat API测试路由和fallback:")

questions = [
    ("红烧肉的历史渊源", "应该走kb-query，从PostgreSQL获取"),
    ("北京烤鸭的制作工艺", "可能走kb-query，PostgreSQL没有则从Milvus获取"),
    ("锅包肉的历史", "可能走kb-query，测试Milvus fallback")
]

for q, desc in questions:
    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={"message": q, "session_id": "_test_fallback"}
    )

    if response.status_code == 200:
        data = response.json()
        route = data.get("route")
        sources = len(data.get("sources", []))
        answer_len = len(data.get("message", ""))

        print(f"\n   问题: {q}")
        print(f"   路由: {route}")
        print(f"   Sources: {sources}")
        print(f"   答案长度: {answer_len} 字符")
        print(f"   说明: {desc}")
    else:
        print(f"\n   错误: {q} - {response.status_code}")

print("\n" + "=" * 60)
print("测试结论:")
print("1. 如果PostgreSQL有数据，kb-query会优先使用PostgreSQL")
print("2. 如果PostgreSQL没有数据，kb-query应该fallback到Milvus")
print("3. 如果都没有数据，可能路由到graphrag-query或返回空结果")
print("=" * 60)
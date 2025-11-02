#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接测试kb_ingest返回的原始数据"""

import requests
import json

print("=" * 60)
print("测试kb_ingest原始响应")
print("=" * 60)

# 测试查询
query = "东坡肉的历史"
url = "http://localhost:8100/api/v1/knowledge/search"

payload = {
    "query": query,
    "top_k": 3,
}

response = requests.post(url, json=payload)

print(f"状态码: {response.status_code}")

if response.status_code == 200:
    body = response.json()
    data_results = body.get("results", [])

    print(f"\n返回结果数量: {len(data_results)}")

    # 模拟local_search中的处理
    postgres_results = []

    for i, item in enumerate(data_results, 1):
        print(f"\n结果 {i}:")
        print(f"  所有字段: {list(item.keys())}")

        # 检查关键字段
        print(f"  document_id: {item.get('document_id', 'MISSING')}")
        print(f"  source: {item.get('source', 'MISSING')}")
        print(f"  score: {item.get('score', 'MISSING')}")

        # 检查metadata
        metadata = item.get("metadata", {})
        if metadata:
            print(f"  metadata字段: {list(metadata.keys())}")
            print(f"  菜品名称: {metadata.get('菜品名称', 'None')}")
            print(f"  朝代: {metadata.get('朝代', 'None')}")

        # 模拟添加tool字段
        item_copy = dict(item)
        metadata_copy = dict(item_copy.get("metadata") or {})
        item_copy["metadata"] = metadata_copy
        item_copy["tool"] = "postgres"
        postgres_results.append(item_copy)

        print(f"  添加tool字段后: {item_copy.get('tool')}")

    # 测试_collect_sources函数的逻辑
    print("\n" + "=" * 60)
    print("测试sources收集逻辑")
    print("=" * 60)

    collected_sources = []

    for doc in postgres_results:
        meta = doc.get("metadata") or {}
        candidate = (
            doc.get("source")
            or doc.get("source_table")
            or meta.get("source")
            or meta.get("source_table")
            or meta.get("url")
            or meta.get("title")
        )
        print(f"\n文档 {doc.get('document_id', 'N/A')}:")
        print(f"  doc.source: {doc.get('source')}")
        print(f"  meta.source: {meta.get('source')}")
        print(f"  candidate: {candidate}")

        if candidate:
            collected_sources.append(str(candidate))

    # 去重
    unique_sources = list(dict.fromkeys(collected_sources))
    print(f"\n收集到的sources: {unique_sources}")

else:
    print(f"错误: {response.status_code}")
    print(f"响应: {response.text}")
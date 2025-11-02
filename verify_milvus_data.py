#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify data in Milvus"""

import requests
import json

headers = {"Content-Type": "application/json"}

# Test searches
test_queries = [
    {"query": "东坡肉", "expected": "东坡肉"},
    {"query": "麻婆豆腐", "expected": "麻婆豆腐"},
    {"query": "佛跳墙", "expected": "佛跳墙"},
    {"query": "宋代名菜", "expected": "东坡肉"},
    {"query": "历史菜谱", "expected": None}
]

print("Verifying Milvus data:")
print("=" * 50)

for test in test_queries:
    response = requests.post(
        "http://localhost:8000/api/v1/knowledge/search",
        headers=headers,
        json={"query": test["query"], "top_k": 3}
    )

    results = response.json().get('results', [])

    print(f"\nQuery: {test['query']}")
    print(f"Results: {len(results)} found")

    for i, result in enumerate(results[:2]):
        name = result.get('metadata', {}).get('name', 'N/A')
        score = result.get('score', 0)
        content_preview = result.get('content', '')[:100]
        print(f"  {i+1}. {name} (score: {score:.3f})")
        print(f"     {content_preview}...")

# Get total count
print("\n" + "=" * 50)
print("Total search for all historical dishes:")
response = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    headers=headers,
    json={"query": "历史 名菜 朝代", "top_k": 20}
)

results = response.json().get('results', [])
print(f"Found {len(results)} historical recipe entries")
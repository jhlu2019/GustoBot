#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试配置更新后的kb-query功能"""

import requests
import json
import time

print("=" * 60)
print("测试配置更新后的知识库功能")
print("=" * 60)

# 1. 测试 kb_ingest API
print("\n1. 测试 kb_ingest 搜索API")
print("-" * 40)

try:
    response = requests.post(
        "http://localhost:8100/api/search",
        headers={"Content-Type": "application/json"},
        json={
            "query": "东坡肉",
            "top_k": 5,
            "source_tables": ["historical_recipes"]
        }
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        results = response.json()
        print(f"✓ 搜索成功！找到 {len(results.get('results', []))} 条结果")
        for i, r in enumerate(results[:2]):
            print(f"\n结果 {i+1}:")
            print(f"  内容: {r.get('content', '')[:100]}...")
            print(f"  相似度: {r.get('similarity', 0):.3f}")
    else:
        print(f"✗ 搜索失败: {response.text}")
except Exception as e:
    print(f"✗ 异常: {e}")

# 2. 测试 kb-query 路由
print("\n\n2. 测试 kb-query 路由")
print("-" * 40)

test_questions = [
    "东坡肉的历史是什么？",
    "麻婆豆腐的来历",
    "宫保鸡丁是哪个朝代的菜？"
]

for i, question in enumerate(test_questions, 1):
    print(f"\n测试 {i}: {question}")

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={
            "message": question,
            "session_id": f"test_kb_config_{i}"
        }
    )

    if response.status_code == 200:
        result = response.json()
        route = result.get('route', 'N/A')
        print(f"  路由: {route}")

        if route == 'kb-query':
            print("  ✓ 成功路由到 kb-query")

            # 检查回答内容
            answer = result.get('message', '')
            if '暂未找到' in answer:
                print("  ⚠ 未找到相关数据")
            else:
                print(f"  ✓ 获得回答 (长度: {len(answer)})")
                print(f"  预览: {answer[:100]}...")

            # 检查数据源
            if result.get('sources'):
                print(f"  ✓ 数据源: {len(result['sources'])} 个")
        else:
            print(f"  ⚠ 路由到: {route}")
    else:
        print(f"  ✗ 错误: {response.status_code}")

# 3. 检查日志
print("\n\n3. 检查最近的日志")
print("-" * 40)

import subprocess

# 检查 backend 日志中的 PostgreSQL 相关信息
cmd = "docker-compose logs backend --tail 50 | grep -E '(Postgres|postgres|kb_ingest)' | tail -5"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

if result.stdout:
    print("Backend 日志片段:")
    for line in result.stdout.strip().split('\n')[-3:]:
        if line:
            print(f"  {line}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
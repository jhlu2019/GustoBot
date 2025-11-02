#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试kb-query是否能查询PostgreSQL数据"""

import requests
import json

# 测试历史相关的查询
test_questions = [
    "东坡肉的历史是什么？",
    "东坡肉是谁发明的？",
    "麻婆豆腐的来历",
    "佛跳墙有什么历史典故？",
    "宫保鸡丁是哪个朝代的菜？"
]

print("=" * 60)
print("测试 kb-query 对 PostgreSQL 历史数据的查询")
print("=" * 60)

for i, question in enumerate(test_questions, 1):
    print(f"\n测试 {i}: {question}")
    print("-" * 50)

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={
            "message": question,
            "session_id": f"test_kb_postgres_{i}"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"路由类型: {result.get('route', 'N/A')}")
        print(f"路由逻辑: {result.get('route_logic', 'N/A')[:100]}...")

        # 检查是否来自kb-query
        if result.get('route') == 'kb-query':
            print("✅ 成功路由到 kb-query")

            # 检查是否有数据来源
            if result.get('sources'):
                print(f"✅ 找到数据源: {len(result['sources'])} 个")
            else:
                print("⚠️ 未返回具体数据源")

        # 显示部分回答
        answer = result.get('message', '')
        print(f"回答: {answer[:200]}...")

    else:
        print(f"❌ 错误: {response.status_code}")
        print(response.text)

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

# 直接测试 kb_ingest 服务
print("\n\n额外测试: 直接查询 PostgreSQL")
print("-" * 50)

# 测试通过 kb_ingest 服务查询
try:
    # 查询东坡肉
    response = requests.post(
        "http://localhost:8100/api/search",
        headers={"Content-Type": "application/json"},
        json={
            "query": "东坡肉",
            "table": "historical_recipes"
        }
    )

    if response.status_code == 200:
        results = response.json()
        print(f"✅ kb_ingest 查询成功，返回 {len(results.get('results', []))} 条结果")
        for result in results.get('results', [])[:2]:
            print(f"  - {result.get('dish_name', 'N/A')}: {result.get('historical_source', 'N/A')[:50]}...")
    else:
        print(f"❌ kb_ingest 查询失败: {response.status_code}")

except Exception as e:
    print(f"❌ kb_ingest 服务不可用: {e}")
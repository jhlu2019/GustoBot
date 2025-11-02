#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试kb-query查询PostgreSQL数据"""

import requests
import json

# 测试问题
questions = [
    "东坡肉的历史",
    "麻婆豆腐的来历",
    "佛跳墙的历史典故"
]

print("Testing kb-query with PostgreSQL data")
print("=" * 50)

results = []
for q in questions:
    print(f"\nQ: {q}")

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={"message": q, "session_id": "test_pg"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Route: {data.get('route')}")

        if data.get('route') == 'kb-query':
            print("Status: SUCCESS - Routed to kb-query")

            # 检查回答内容
            answer = data.get('message', '')
            if '东坡' in answer or '苏轼' in answer:
                print("Status: Found relevant content in PostgreSQL")
            elif '暂未找到' in answer:
                print("Status: No data found")
        else:
            print(f"Status: Routed to {data.get('route')} instead")
    else:
        print(f"Error: {response.status_code}")

# 额外测试：直接查询PostgreSQL
print("\n\nDirect PostgreSQL test:")
print("-" * 30)

# 通过容器直接查询
cmd = """docker exec -i gustobot-kb_postgres-1 psql -U postgres -d vector_db -c "SELECT dish_name, dynasty, historical_source FROM historical_recipes WHERE dish_name LIKE '%东坡%' OR dish_name LIKE '%麻婆%' LIMIT 3;" """
print("Querying PostgreSQL directly...")
import subprocess
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
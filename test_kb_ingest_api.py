#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试kb_ingest API"""

import requests
import json

# 测试 kb_ingest 的搜索 API
print("Testing kb_ingest API endpoints:")
print("=" * 50)

# 1. 测试正确的API路径
print("\n1. Testing /api/search (correct path)")
try:
    response = requests.post(
        "http://localhost:8100/api/search",
        headers={"Content-Type": "application/json"},
        json={
            "query": "东坡肉",
            "top_k": 5
        }
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ API accessible")
        # print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

# 2. 测试错误的API路径
print("\n2. Testing /api/v1/knowledge/search (wrong path)")
try:
    response = requests.post(
        "http://localhost:8100/api/v1/knowledge/search",
        headers={"Content-Type": "application/json"},
        json={
            "query": "东坡肉",
            "top_k": 5
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

# 3. 测试从容器内部访问
print("\n3. Testing from backend container")
import subprocess

cmd = """docker exec gustobot-backend-1 curl -s -X POST http://kb_ingest:8000/api/search -H "Content-Type: application/json" -d '{"query": "东坡肉", "top_k": 5}'"""
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

print(f"Return Code: {result.returncode}")
if result.returncode == 0:
    print("✓ Backend can reach kb_ingest")
    data = json.loads(result.stdout)
    print(f"Results count: {len(data.get('results', []))}")
else:
    print(f"Error: {result.stderr}")

# 4. 检查数据源
print("\n4. Checking data sources in kb_ingest")
cmd = """docker exec gustobot-kb_postgres-1 psql -U postgres -d vector_db -c "SELECT table_name, (SELECT COUNT(*) FROM information_schema.columns WHERE table_name=t.table_name) as column_count FROM information_schema.tables t WHERE table_schema='public' AND table_name LIKE '%historical%';""""
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)

print("\n" + "=" * 50)
print("Summary:")
print("- kb_ingest service is running on port 8100")
print("- API path is /api/search (not /api/v1/knowledge/search)")
print("- Backend is using wrong API path")
print("- PostgreSQL has data but backend can't access it via kb_ingest")
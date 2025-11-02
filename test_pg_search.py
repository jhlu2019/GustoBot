#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试PostgreSQL搜索功能"""

import requests
import json

# 测试搜索
test_data = {
    "query": "东坡肉",
    "source_tables": ["historical_recipes"],
    "top_k": 5
}

response = requests.post(
    "http://localhost:8100/api/search",
    headers={"Content-Type": "application/json"},
    json=test_data
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
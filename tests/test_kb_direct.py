#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct test of knowledge base search via API"""

import requests
import json

# Test direct knowledge base search
response = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    headers={"Content-Type": "application/json"},
    json={
        "query": "宫保鸡丁",
        "top_k": 5
    }
)

print("Direct KB Search Results:")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
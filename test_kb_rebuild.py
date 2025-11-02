#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test kb-query functionality after Milvus rebuild"""

import requests
import json

# Test kb-query with a question about the recipe we just added
response = requests.post(
    "http://localhost:8000/api/v1/chat/",
    headers={"Content-Type": "application/json"},
    json={
        "message": "宫保鸡丁的历史是什么",
        "session_id": "test_kb_after_rebuild"
    }
)

print("Status Code:", response.status_code)
print("Response:")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
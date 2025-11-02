#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test kb-query with recipe-related questions"""

import requests
import json

# Test questions about the recipe we added
test_questions = [
    "宫保鸡丁需要哪些食材？",
    "宫保鸡丁怎么做？",
    "宫保鸡丁有什么烹饪技巧？"
]

for question in test_questions:
    print(f"\nQuestion: {question}")
    print("-" * 50)

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={
            "message": question,
            "session_id": "test_kb_simple"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Route: {result['route']}")
        print(f"Answer: {result['message'][:200]}...")
        if result.get('sources'):
            print(f"Sources: {len(result['sources'])} found")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correct batch import to Milvus"""

import requests
import json
import pandas as pd
import time

# Read Excel
df = pd.read_excel(r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx')
df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

# Prepare recipes list
recipes = []
for i, (_, row) in enumerate(df.iterrows()):
    # Create a description that combines all info
    description = f"""
菜品名称: {row['dish_name']}
历史源头: {row['historical_source']}
朝代: {row['dynasty']}
地区: {row['region']}
创始人: {row['originator']}
历史描述: {row['historical_description']}
    """.strip()

    recipe = {
        "id": f"historical_{i}",
        "name": row['dish_name'],
        "category": f"{row['dynasty']}名菜",
        "difficulty": "传统",
        "ingredients": [],
        "steps": [],
        "tips": description
    }
    recipes.append(recipe)

# Import directly as array (not wrapped in object)
API_URL = "http://localhost:8000/api/v1/knowledge/recipes/batch"
headers = {"Content-Type": "application/json"}

print(f"Importing {len(recipes)} historical recipes to Milvus...")
print(f"API URL: {API_URL}")

# Make the request with array directly
response = requests.post(API_URL, headers=headers, json=recipes)

print(f"\nStatus Code: {response.status_code}")
if response.status_code == 201:
    print("✓ Import successful!")
    result = response.json()
    print(f"Response: {result}")
else:
    print(f"✗ Import failed")
    print(f"Error: {response.text}")

# Verify by searching
print("\nVerifying import...")
time.sleep(1)

test_searches = ["东坡肉", "麻婆豆腐", "佛跳墙", "红烧肉"]
for item in test_searches:
    search_resp = requests.post(
        "http://localhost:8000/api/v1/knowledge/search",
        headers=headers,
        json={"query": item, "top_k": 2}
    )
    results = search_resp.json().get('results', [])
    print(f"\nSearch '{item}': {len(results)} results found")
    if results:
        for r in results[:1]:
            name = r.get('metadata', {}).get('name', 'N/A')
            score = r.get('score', 0)
            print(f"  - {name} (score: {score:.3f})")

# Save imported data
with open('imported_historical_recipes.json', 'w', encoding='utf-8') as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print(f"\nData saved to imported_historical_recipes.json")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple batch import to Milvus"""

import requests
import json
import pandas as pd
import time

# Read Excel
df = pd.read_excel(r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx')
df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

# Prepare recipes
recipes = []
for i, (_, row) in enumerate(df.iterrows()):
    content = f"{row['dish_name']} - {row['historical_source']} - {row['dynasty']} - {row['historical_description']}"

    recipe = {
        "id": f"hist_{i}_{int(time.time())}",
        "name": row['dish_name'],
        "category": "历史名菜",
        "difficulty": "未知",
        "ingredients": [],
        "steps": [],
        "tips": content
    }
    recipes.append(recipe)

print(f"Total recipes to import: {len(recipes)}")

# Import in batches
API_URL = "http://localhost:8000/api/v1/knowledge/recipes/batch"
headers = {"Content-Type": "application/json"}

# Check current data first
print("\nChecking current data in Milvus...")
search_resp = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    headers=headers,
    json={"query": "东坡肉", "top_k": 1}
)
print(f"Current search results: {len(search_resp.json().get('results', []))} items")

# Import all recipes in one batch
print("\nImporting all recipes...")
response = requests.post(API_URL, headers=headers, json={"recipes": recipes})

print(f"\nImport Status Code: {response.status_code}")
if response.status_code in [200, 201]:
    print("Import successful!")
    print(f"Response: {response.text[:200]}...")
else:
    print(f"Import failed: {response.text}")

# Verify import
print("\nVerifying import...")
time.sleep(2)

# Search for historical recipes
search_queries = ["东坡肉", "麻婆豆腐", "佛跳墙"]
for query in search_queries:
    resp = requests.post(
        "http://localhost:8000/api/v1/knowledge/search",
        headers=headers,
        json={"query": query, "top_k": 2}
    )
    results = resp.json().get('results', [])
    print(f"\nSearch '{query}': Found {len(results)} results")
    if results:
        print(f"  First result: {results[0].get('metadata', {}).get('name', 'N/A')}")

# Save data
with open('historical_recipes_batch.json', 'w', encoding='utf-8') as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print("\nData saved to historical_recipes_batch.json")
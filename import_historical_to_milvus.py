#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将历史菜谱数据批量导入到 Milvus"""

import requests
import json
import pandas as pd
import time

# 读取Excel文件
excel_path = r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx'
df = pd.read_excel(excel_path)

# 清理列名
df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

# 准备批量导入的数据
recipes = []
for _, row in df.iterrows():
    # 构建完整的描述
    content = f"""{row['dish_name']}
历史源头: {row['historical_source']}
朝代: {row['dynasty']}
地区: {row['region']}
创始人: {row['originator']}
历史描述: {row['historical_description']}"""

    recipe = {
        "id": f"historical_{_}_{int(time.time())}",
        "name": row['dish_name'],
        "category": f"{row['dynasty']}菜",
        "difficulty": "未知",
        "ingredients": [],
        "steps": [],
        "tips": content
    }
    recipes.append(recipe)

print(f"准备导入 {len(recipes)} 条历史菜谱数据到 Milvus")

# 批量导入到 Milvus
batch_size = 3  # 每批3条
success_count = 0
error_count = 0

for i in range(0, len(recipes), batch_size):
    batch = recipes[i:i+batch_size]
    print(f"\n导入批次 {i//batch_size + 1}/{(len(recipes)-1)//batch_size + 1}")

    # 批量导入
    response = requests.post(
        "http://localhost:8000/api/v1/knowledge/recipes/batch",
        headers={"Content-Type": "application/json"},
        json={"recipes": batch}
    )

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ 成功导入 {len(batch)} 条数据")
        success_count += len(batch)
        if 'message' in result:
            print(f"   {result['message']}")
    else:
        print(f"❌ 导入失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        error_count += len(batch)

    # 短暂延迟避免请求过快
    time.sleep(1)

print(f"\n导入完成！成功: {success_count}, 失败: {error_count}")

# 保存导入记录
with open('historical_recipes_imported.json', 'w', encoding='utf-8') as f:
    json.dump(recipes, f, ensure_ascii=False, indent=2)

print("\n数据已保存到 historical_recipes_imported.json")
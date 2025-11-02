#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成PostgreSQL pgvector插入SQL"""

import pandas as pd
import numpy as np

# 读取Excel
df = pd.read_excel(r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx')
df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

print("-- PostgreSQL pgvector 插入脚本")
print("-- 注意：这里使用随机向量作为示例，实际应该使用真实的embedding")
print()

# 生成插入语句
print("INSERT INTO historical_recipes_pgvector (dish_name, historical_source, dynasty, region, originator, historical_description, content_text, embedding) VALUES")

values = []
for idx, row in df.iterrows():
    # 构建内容文本
    content_text = f"""菜品名称: {row['dish_name']}
历史源头: {row['historical_source']}
朝代: {row['dynasty']}
地区: {row['region']}
创始人: {row['originator']}
历史描述: {row['historical_description']}""".strip().replace("'", "''")

    # 生成1024维随机向量（示例）
    vector = np.random.random(1024).round(6)
    vector_str = "[" + ",".join(map(str, vector)) + "]"

    # SQL值
    value = f"""(\
'{row['dish_name']}', \
'{str(row['historical_source']).replace("'", "''")}', \
'{str(row['dynasty'])}', \
'{str(row['region'])}', \
'{str(row['originator'])}', \
'{str(row['historical_description']).replace("'", "''")}', \
'{content_text}', \
'{vector_str}'::vector)"""

    values.append(value)

print(",\n".join(values) + ";")
print()
print(f"-- 共插入 {len(values)} 条记录")
print()
print("-- 验证查询")
print("SELECT COUNT(*) FROM historical_recipes_pgvector;")
print()
print("-- 测试搜索")
print("SELECT dish_name, dynasty FROM historical_recipes_pgvector WHERE dish_name LIKE '%东坡肉%';")
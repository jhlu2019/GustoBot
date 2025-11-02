#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将Excel数据转换为SQL插入语句"""

import pandas as pd
import json

# 读取Excel文件
excel_path = r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx'
df = pd.read_excel(excel_path)

# 清理列名
df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

# 生成SQL插入语句
sql_statements = []
for _, row in df.iterrows():
    # 转义单引号
    dish_name = str(row['dish_name']).replace("'", "''") if pd.notna(row['dish_name']) else None
    historical_source = str(row['historical_source']).replace("'", "''") if pd.notna(row['historical_source']) else None
    dynasty = str(row['dynasty']).replace("'", "''") if pd.notna(row['dynasty']) else None
    region = str(row['region']).replace("'", "''") if pd.notna(row['region']) else None
    originator = str(row['originator']).replace("'", "''") if pd.notna(row['originator']) else None
    historical_description = str(row['historical_description']).replace("'", "''") if pd.notna(row['historical_description']) else None

    sql = f"""INSERT INTO historical_recipes (dish_name, historical_source, dynasty, region, originator, historical_description) VALUES ('{dish_name}', '{historical_source}', '{dynasty}', '{region}', '{originator}', '{historical_description}');"""
    sql_statements.append(sql)

# 保存SQL文件
with open('import_historical_recipes.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql_statements))

print(f"生成了 {len(sql_statements)} 条SQL插入语句")

# 也保存为JSON格式，方便检查
data = []
for _, row in df.iterrows():
    data.append({
        'dish_name': row['dish_name'],
        'historical_source': row['historical_source'],
        'dynasty': row['dynasty'],
        'region': row['region'],
        'originator': row['originator'],
        'historical_description': row['historical_description']
    })

with open('historical_recipes.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("数据已保存到 historical_recipes.json")
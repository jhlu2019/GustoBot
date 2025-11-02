#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将Excel数据导入到PostgreSQL pgvector表并生成embedding"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import requests
import json
import time

# 配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'postgrespass',
    'database': 'vector_db'
}

# Embedding API配置
EMBEDDING_CONFIG = {
    'api_key': 'sk-9a1262ef1b7144eab84725635a01ac3d',
    'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'model': 'text-embedding-v4'
}

def get_embedding(text):
    """获取文本的embedding向量"""
    headers = {
        'Authorization': f'Bearer {EMBEDDING_CONFIG["api_key"]}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': EMBEDDING_CONFIG['model'],
        'input': text,
        'encoding_format': 'float'
    }

    response = requests.post(
        f"{EMBEDDING_CONFIG['base_url']}/embeddings",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        return result['data'][0]['embedding']
    else:
        print(f"Embedding API error: {response.status_code} - {response.text}")
        # 返回随机向量作为fallback
        return np.random.random(1024).astype(np.float32).tolist()

def main():
    # 读取Excel文件
    print("读取Excel文件...")
    df = pd.read_excel(r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx')
    df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

    print(f"读取到 {len(df)} 条记录")

    # 连接PostgreSQL
    print("\n连接PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 创建表
    print("\n创建pgvector表...")
    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;

        DROP TABLE IF EXISTS historical_recipes_pgvector;
        CREATE TABLE historical_recipes_pgvector (
            id SERIAL PRIMARY KEY,
            dish_name VARCHAR(200) NOT NULL,
            historical_source TEXT,
            dynasty VARCHAR(50),
            region VARCHAR(100),
            originator VARCHAR(100),
            historical_description TEXT,
            content_text TEXT,
            embedding vector(1024),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX ON historical_recipes_pgvector USING ivfflat (embedding vector_cosine_ops);
    """)
    conn.commit()

    # 处理并插入数据
    print("\n处理数据并生成embedding...")
    inserted = 0

    for idx, row in df.iterrows():
        # 构建搜索内容
        content_text = f"""
菜品名称: {row['dish_name']}
历史源头: {row['historical_source']}
朝代: {row['dynasty']}
地区: {row['region']}
创始人: {row['originator']}
历史描述: {row['historical_description']}
        """.strip()

        print(f"\n处理 {idx+1}/8: {row['dish_name']}")
        print(f"生成embedding...")

        # 获取embedding
        embedding = get_embedding(content_text)

        # 插入数据库
        cur.execute("""
            INSERT INTO historical_recipes_pgvector
            (dish_name, historical_source, dynasty, region, originator,
             historical_description, content_text, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['dish_name'],
            str(row['historical_source']),
            str(row['dynasty']),
            str(row['region']),
            str(row['originator']),
            str(row['historical_description']),
            content_text,
            embedding
        ))

        inserted += 1
        print(f"✓ 已插入")
        time.sleep(0.5)  # 避免API限制

    conn.commit()
    print(f"\n成功插入 {inserted} 条记录")

    # 验证
    cur.execute("SELECT COUNT(*) FROM historical_recipes_pgvector")
    count = cur.fetchone()[0]
    print(f"\n表中共有 {count} 条记录")

    # 测试向量搜索
    print("\n测试向量搜索...")
    query_embedding = get_embedding("东坡肉")

    cur.execute("""
        SELECT dish_name, dynasty,
               1 - (embedding <=> %s::vector) as similarity
        FROM historical_recipes_pgvector
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (query_embedding, query_embedding))

    results = cur.fetchall()
    print("\n最相似的记录:")
    for name, dynasty, similarity in results:
        print(f"- {name} ({dynasty}) - 相似度: {similarity:.3f}")

    conn.close()
    print("\n完成！")

if __name__ == "__main__":
    main()
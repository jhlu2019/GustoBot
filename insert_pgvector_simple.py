#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple insert to pgvector using psycopg2"""

import psycopg2
import numpy as np
import subprocess
import json

# DB配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'postgrespass',
    'database': 'vector_db'
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 首先启用pgvector扩展
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    # 创建表
    cur.execute("""
        DROP TABLE IF EXISTS historical_recipes_vector;
        CREATE TABLE historical_recipes_vector (
            id SERIAL PRIMARY KEY,
            source_table VARCHAR(100),
            source_id VARCHAR(100),
            content TEXT,
            embedding vector(1024)
        );
    """)
    conn.commit()

    # 获取处理后的数据
    print("Fetching processed data...")
    result = subprocess.run(
        ["docker", "exec", "gustobot-kb_ingest-1", "cat", "save/20251102_070331/processed_data.csv"],
        capture_output=True, text=True, encoding='utf-8'
    )

    lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行

    print(f"Processing {len(lines)} records...")

    # 处理并插入数据
    for i, line in enumerate(lines):
        # 解析CSV行（简单处理）
        parts = line.split('","')
        if len(parts) < 4:
            continue

        # 提取内容
        content = parts[3].strip('"')  # rewritten_content字段

        # 创建示例embedding（1024维）
        embedding = np.random.random(1024).astype(np.float32)

        # 插入数据库
        cur.execute("""
            INSERT INTO historical_recipes_vector
            (source_table, source_id, content, embedding)
            VALUES (%s, %s, %s, %s)
        """, ("Sheet1", str(i), content, embedding.tolist()))

    conn.commit()
    print(f"Inserted {len(lines)} records")

    # 验证
    cur.execute("SELECT COUNT(*) FROM historical_recipes_vector")
    count = cur.fetchone()[0]
    print(f"Total records: {count}")

    # 测试相似度搜索
    print("\nTesting similarity search...")
    query_embedding = np.random.random(1024).astype(np.float32)

    cur.execute("""
        SELECT content,
               (embedding <=> %s::vector) as distance
        FROM historical_recipes_vector
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (query_embedding.tolist(), query_embedding.tolist()))

    results = cur.fetchall()
    for content, distance in results:
        print(f"  Distance: {distance:.3f}")
        print(f"  Content: {content[:80]}...")

    conn.close()

if __name__ == "__main__":
    main()
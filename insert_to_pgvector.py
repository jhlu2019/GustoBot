#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将处理后的数据插入到PostgreSQL pgvector"""

import psycopg2
import numpy as np
from pgvector.psycopg import register_vector
import requests
import json

# PostgreSQL连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'postgrespass',
    'database': 'vector_db'
}

def create_embedding_vector():
    """创建一个示例的1024维向量（实际应该使用真实的embedding）"""
    # 这里使用随机向量作为示例
    # 实际使用时应该调用embedding API
    return np.random.random(1024).astype(np.float32).tolist()

def main():
    # 连接数据库
    conn = psycopg2.connect(**DB_CONFIG)
    register_vector(conn)
    cur = conn.cursor()

    # 创建pgvector表（如果不存在）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historical_recipes_vector (
            id SERIAL PRIMARY KEY,
            source_table VARCHAR(100),
            source_id VARCHAR(100),
            original_data JSONB,
            rewritten_content TEXT,
            embedding vector(1024),
            company_name VARCHAR(100),
            report_year VARCHAR(10),
            processed_time TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_historical_recipes_vector_embedding
        ON historical_recipes_vector
        USING ivfflat (embedding vector_cosine_ops);
    """)
    conn.commit()

    # 从容器获取处理后的数据
    cmd = "docker exec gustobot-kb_ingest-1 cat save/20251102_070331/processed_data.csv"
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

    lines = result.stdout.strip().split('\n')
    headers = lines[0].split(',')

    print(f"Processing {len(lines)-1} records...")

    inserted = 0
    for line in lines[1:]:
        values = line.split(',', maxsplit=7)  # 最多分割8次
        if len(values) < 8:
            continue

        source_table = values[0]
        source_id = values[1]
        original_data = values[2]
        rewritten_content = values[3]
        company_name = values[4] if values[4] else None
        report_year = values[5] if values[5] else None
        processed_time = values[6] if values[6] else None

        # 创建embedding（这里使用示例，实际应该调用API）
        embedding = create_embedding_vector()

        # 插入数据
        cur.execute("""
            INSERT INTO historical_recipes_vector
            (source_table, source_id, original_data, rewritten_content,
             embedding, company_name, report_year, processed_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            source_table, source_id, original_data, rewritten_content,
            embedding, company_name, report_year, processed_time
        ))

        inserted += 1

    conn.commit()
    print(f"Successfully inserted {inserted} records")

    # 验证插入
    cur.execute("SELECT COUNT(*) FROM historical_recipes_vector")
    count = cur.fetchone()[0]
    print(f"Total records in table: {count}")

    # 测试搜索
    print("\nTesting vector search...")
    # 创建一个测试查询向量
    query_embedding = create_embedding_vector()

    cur.execute("""
        SELECT rewritten_content,
               1 - (embedding <=> %s::vector) as similarity
        FROM historical_recipes_vector
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (query_embedding, query_embedding))

    results = cur.fetchall()
    print(f"Found {len(results)} similar records:")
    for content, similarity in results:
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Content: {content[:100]}...")

    conn.close()

if __name__ == "__main__":
    main()
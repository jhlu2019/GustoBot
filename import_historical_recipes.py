#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入历史菜谱数据到PostgreSQL"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'postgrespass',
    'database': 'vector_db'
}

def create_table(conn):
    """创建历史菜谱表"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_recipes (
                id SERIAL PRIMARY KEY,
                dish_name TEXT NOT NULL,
                historical_source TEXT,
                dynasty TEXT,
                region TEXT,
                originator TEXT,
                historical_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 创建全文搜索索引
            CREATE INDEX IF NOT EXISTS idx_historical_recipes_search ON historical_recipes
            USING gin(to_tsvector('chinese', dish_name || ' ' ||
                               COALESCE(historical_source, '') || ' ' ||
                               COALESCE(historical_description, '')));

            -- 创建向量列（用于未来的向量搜索）
            ALTER TABLE historical_recipes
            ADD COLUMN IF NOT EXISTS embedding vector(1024);
        """)
        conn.commit()
        print("✅ 表创建成功")

def import_data(conn, excel_path):
    """导入Excel数据"""
    # 读取Excel文件
    df = pd.read_excel(excel_path)

    # 清理列名
    df.columns = ['dish_name', 'historical_source', 'dynasty', 'region', 'originator', 'historical_description']

    # 导入数据
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO historical_recipes
                (dish_name, historical_source, dynasty, region, originator, historical_description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                row['dish_name'],
                row['historical_source'],
                row['dynasty'],
                row['region'],
                row['originator'],
                row['historical_description']
            ))

        conn.commit()
        print(f"✅ 成功导入 {len(df)} 条数据")

def test_search(conn):
    """测试搜索功能"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 测试全文搜索
        cur.execute("""
            SELECT dish_name, dynasty, region, historical_source,
                   ts_rank(to_tsvector('chinese', dish_name || ' ' ||
                          COALESCE(historical_source, '') || ' ' ||
                          COALESCE(historical_description, '')),
                          plainto_tsquery('chinese', %s)) as rank
            FROM historical_recipes
            WHERE to_tsvector('chinese', dish_name || ' ' ||
                  COALESCE(historical_source, '') || ' ' ||
                  COALESCE(historical_description, '')) @@ plainto_tsquery('chinese', %s)
            ORDER BY rank DESC
            LIMIT 5;
        """, ("东坡肉", "东坡肉"))

        results = cur.fetchall()

        print("\n🔍 搜索结果（东坡肉）:")
        for row in results:
            print(f"- {row['dish_name']} ({row['dynasty']}, {row['region']})")
            print(f"  来源: {row['historical_source'][:50]}...")
            print(f"  相关度: {row['rank']:.2f}\n")

def main():
    excel_path = r'F:\pythonproject\GustoBot\data\kb\历史菜谱源头.xlsx'

    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 连接PostgreSQL成功")

        # 创建表
        create_table(conn)

        # 导入数据
        import_data(conn, excel_path)

        # 测试搜索
        test_search(conn)

        conn.close()
        print("\n✅ 导入完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
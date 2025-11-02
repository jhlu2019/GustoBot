#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证数据导入情况 - Neo4j, MySQL, PostgreSQL"""

import asyncio
import psycopg2
import mysql.connector
from neo4j import GraphDatabase
import requests
import json
from datetime import datetime

def check_postgres_data():
    """检查 PostgreSQL 数据"""
    print("=" * 60)
    print("PostgreSQL (pgvector) 数据检查")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="vector_db",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()

        # 检查 pgvector 扩展
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cursor.fetchone()
        print(f"✓ pgvector 扩展: {'已安装' if vector_ext else '未安装'}")

        # 检查表是否存在
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'searchable_documents';
        """)
        table_exists = cursor.fetchone()
        print(f"✓ searchable_documents 表: {'存在' if table_exists else '不存在'}")

        if table_exists:
            # 检查数据量
            cursor.execute("SELECT COUNT(*) FROM searchable_documents;")
            count = cursor.fetchone()[0]
            print(f"✓ 数据量: {count} 条记录")

            # 检查最近的几条数据
            if count > 0:
                cursor.execute("""
                    SELECT document_id, source, LEFT(content, 50) as content_preview
                    FROM searchable_documents
                    ORDER BY created_at DESC
                    LIMIT 5;
                """)
                records = cursor.fetchall()
                print("\n最近的 5 条记录:")
                for i, (doc_id, source, content) in enumerate(records, 1):
                    print(f"  {i}. 来源: {source}")
                    print(f"     内容: {content}...")
                    print(f"     ID: {doc_id}")
                    print()

        conn.close()
        return True
    except Exception as e:
        print(f"✗ PostgreSQL 连接失败: {e}")
        return False

def check_mysql_data():
    """检查 MySQL 数据"""
    print("=" * 60)
    print("MySQL 数据检查")
    print("=" * 60)

    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=13306,
            user="recipe_user",
            password="recipepass",
            database="recipe_db"
        )
        cursor = conn.cursor()

        # 检查表
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"✓ 表数量: {len(tables)} 个")

        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} 条记录")

        # 检查具体的菜谱数据
        cursor.execute("SELECT name, category FROM recipes LIMIT 5;")
        recipes = cursor.fetchall()
        if recipes:
            print("\n示例菜谱:")
            for name, category in recipes:
                print(f"  - {name} ({category})")

        conn.close()
        return True
    except Exception as e:
        print(f"✗ MySQL 连接失败: {e}")
        return False

def check_neo4j_data():
    """检查 Neo4j 数据"""
    print("=" * 60)
    print("Neo4j 数据检查")
    print("=" * 60)

    try:
        driver = GraphDatabase.driver("bolt://localhost:17687", auth=("neo4j", "recipepass"))
        with driver.session() as session:
            # 检查节点数量
            result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count")
            nodes = {}
            for record in result:
                label = record["label"][0] if record["label"] else "Unknown"
                count = record["count"]
                nodes[label] = count
                print(f"✓ {label}: {count} 个节点")

            # 检查关系统计
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            relationships = {}
            for record in result:
                rel_type = record["type"]
                count = record["count"]
                relationships[rel_type] = count
                print(f"✓ {rel_type}: {count} 条关系")

            # 检查具体的菜谱
            if "Dish" in nodes and nodes["Dish"] > 0:
                result = session.run("MATCH (d:Dish) RETURN d.name LIMIT 5")
                dishes = [record["d.name"] for record in result]
                print("\n示例菜谱:")
                for dish in dishes:
                    print(f"  - {dish}")

        driver.close()
        return True
    except Exception as e:
        print(f"✗ Neo4j 连接失败: {e}")
        return False

def check_api_status():
    """检查 API 服务状态"""
    print("=" * 60)
    print("API 服务状态检查")
    print("=" * 60)

    # 检查主服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✓ 主服务 API: {response.status_code}")
    except:
        print("✗ 主服务 API: 连接失败")

    # 检查知识库服务
    try:
        response = requests.get("http://localhost:8100/health", timeout=5)
        print(f"✓ 知识库服务 API: {response.status_code}")
    except:
        print("✗ 知识库服务 API: 连接失败")

def test_kb_query():
    """测试知识库查询"""
    print("=" * 60)
    print("知识库查询测试")
    print("=" * 60)

    test_questions = [
        "东坡肉的历史是什么？",
        "麻婆豆腐的来历",
        "红烧肉怎么做？"
    ]

    for question in test_questions:
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/chat/",
                headers={"Content-Type": "application/json"},
                json={"message": question, "session_id": "verify_test"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                route = data.get("route", "unknown")
                has_sources = bool(data.get("sources"))
                print(f"✓ Q: {question}")
                print(f"  路由: {route}")
                print(f"  有来源: {'是' if has_sources else '否'}")
                if has_sources:
                    print(f"  来源数: {len(data.get('sources', []))}")
            else:
                print(f"✗ Q: {question} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"✗ Q: {question} - 错误: {e}")

def main():
    print("\n" + "=" * 60)
    print("GustoBot 数据导入验证")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # 检查各数据库数据
    pg_ok = check_postgres_data()
    mysql_ok = check_mysql_data()
    neo4j_ok = check_neo4j_data()

    # 检查服务状态
    check_api_status()

    # 测试查询功能
    print("\n")
    test_kb_query()

    # 总结
    print("\n" + "=" * 60)
    print("数据导入总结")
    print("=" * 60)
    print(f"PostgreSQL (pgvector): {'✓ 正常' if pg_ok else '✗ 异常'}")
    print(f"MySQL: {'✓ 正常' if mysql_ok else '✗ 异常'}")
    print(f"Neo4j: {'✓ 正常' if neo4j_ok else '✗ 异常'}")

    if all([pg_ok, mysql_ok, neo4j_ok]):
        print("\n🎉 所有数据库数据导入成功！")
    else:
        print("\n⚠️ 部分数据库可能存在问题，请检查日志。")

if __name__ == "__main__":
    main()
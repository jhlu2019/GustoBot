#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查各个数据库的数据导入情况"""

import pymysql
import psycopg2
import requests
from neo4j import GraphDatabase
import json

def test_mysql():
    """测试MySQL数据"""
    print("=" * 60)
    print("MySQL 数据库检查")
    print("=" * 60)

    try:
        conn = pymysql.connect(
            host='localhost',
            port=13306,
            user='root',
            password='mysql_password',
            database='recipe_db',
            charset='utf8mb4'
        )

        with conn.cursor() as cursor:
            # 检查表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"表数量: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")

            # 检查recipes表数据
            cursor.execute("SELECT COUNT(*) FROM recipes")
            count = cursor.fetchone()[0]
            print(f"\nrecipes表记录数: {count}")

            if count > 0:
                cursor.execute("SELECT id, name, category FROM recipes LIMIT 5")
                samples = cursor.fetchall()
                print("\n示例数据:")
                for s in samples:
                    print(f"  ID: {s[0]}, 名称: {s[1]}, 分类: {s[2]}")

        conn.close()
        print("\n✅ MySQL 连接正常")
        return True

    except Exception as e:
        print(f"\n❌ MySQL 连接失败: {e}")
        return False


def test_postgres():
    """测试PostgreSQL (pgvector)数据"""
    print("\n" + "=" * 60)
    print("PostgreSQL (pgvector) 数据库检查")
    print("=" * 60)

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='postgres',
            password='postgres',
            database='postgres'
        )

        with conn.cursor() as cursor:
            # 检查表
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            print(f"表数量: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")

            # 检查documents表（KB数据）
            try:
                cursor.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                print(f"\ndocuments表记录数: {count}")

                if count > 0:
                    cursor.execute("SELECT id, document_id, source FROM documents LIMIT 5")
                    samples = cursor.fetchall()
                    print("\n示例数据:")
                    for s in samples:
                        print(f"  ID: {s[0]}, DocID: {s[1]}, Source: {s[2]}")

                # 检查embedding维度
                cursor.execute("""
                    SELECT COUNT(*) FROM documents
                    WHERE embedding IS NOT NULL
                """)
                embedded_count = cursor.fetchone()[0]
                print(f"\n已嵌入向量的记录数: {embedded_count}")

            except Exception as e:
                print(f"\n⚠️ documents表不存在或查询失败: {e}")

        conn.close()
        print("\n✅ PostgreSQL 连接正常")
        return True

    except Exception as e:
        print(f"\n❌ PostgreSQL 连接失败: {e}")
        return False


def test_neo4j():
    """测试Neo4j数据"""
    print("\n" + "=" * 60)
    print("Neo4j 图数据库检查")
    print("=" * 60)

    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

        with driver.session() as session:
            # 检查节点类型和数量
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as label, count(n) as count
                ORDER BY count DESC
            """)

            nodes = result.data()
            print(f"节点类型数量: {len(nodes)}")
            total_nodes = 0
            for node in nodes:
                label = node['label'][0] if node['label'] else '无标签'
                count = node['count']
                total_nodes += count
                print(f"  - {label}: {count} 个")

            print(f"\n总节点数: {total_nodes}")

            # 检查关系类型
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)

            relationships = result.data()
            if relationships:
                print(f"\n关系类型数量: {len(relationships)}")
                total_rels = 0
                for rel in relationships:
                    total_rels += rel['count']
                    print(f"  - {rel['type']}: {rel['count']} 个")
                print(f"\n总关系数: {total_rels}")

            # 检查示例菜品
            if total_nodes > 0:
                result = session.run("""
                    MATCH (d:Dish)
                    RETURN d.name as name, d.category as category
                    LIMIT 5
                """)

                dishes = result.data()
                if dishes:
                    print("\n示例菜品:")
                    for d in dishes:
                        print(f"  - {d['name']} ({d.get('category', 'N/A')})")

        driver.close()
        print("\n✅ Neo4j 连接正常")
        return True

    except Exception as e:
        print(f"\n❌ Neo4j 连接失败: {e}")
        return False


def test_kb_ingest():
    """测试KB Ingest服务"""
    print("\n" + "=" * 60)
    print("KB Ingest 服务检查")
    print("=" * 60)

    try:
        # 测试健康检查
        response = requests.get("http://localhost:8100/health", timeout=5)
        if response.status_code == 200:
            print("✅ KB Ingest 服务运行正常")
        else:
            print(f"⚠️ KB Ingest 健康检查状态码: {response.status_code}")

        # 测试搜索接口
        test_data = {
            "query": "红烧肉",
            "top_k": 3
        }

        response = requests.post(
            "http://localhost:8100/api/v1/knowledge/search",
            json=test_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            results = result.get("results", [])
            print(f"\n搜索结果数量: {len(results)}")

            if results:
                print("\n搜索结果示例:")
                for i, r in enumerate(results[:2], 1):
                    print(f"  {i}. Score: {r.get('score', 0):.3f}")
                    print(f"     Source: {r.get('source', 'N/A')}")
                    print(f"     Content: {r.get('content', '')[:100]}...")

            print("\n✅ KB Ingest 搜索功能正常")
            return True
        else:
            print(f"\n❌ KB Ingest 搜索失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ KB Ingest 服务连接失败: {e}")
        return False


def test_milvus():
    """测试Milvus向量数据库"""
    print("\n" + "=" * 60)
    print("Milvus 向量数据库检查")
    print("=" * 60)

    try:
        from pymilvus import connections, Collection

        # 连接Milvus
        connections.connect(
            alias="default",
            host='localhost',
            port='19530'
        )

        # 检查collection
        try:
            collection = Collection("knowledge_base")
            print(f"✅ Collection 'knowledge_base' 存在")
            print(f"   向量维度: {collection.schema.fields[-1].params['dim']}")
            print(f"   实体数量: {collection.num_entities}")

            if collection.num_entities > 0:
                # 执行测试查询
                import numpy as np
                test_vector = np.random.random((1, 1024)).tolist()

                results = collection.search(
                    data=test_vector,
                    anns_field="embedding",
                    param={"metric_type": "IP", "params": {"nprobe": 10}},
                    limit=3,
                    output_fields=["content", "source"]
                )

                print(f"\n测试搜索返回 {len(results[0])} 个结果")
                if results[0]:
                    print("\nMilvus搜索结果示例:")
                    for i, r in enumerate(results[0][:2], 1):
                        print(f"  {i}. Score: {r.distance:.3f}")
                        print(f"     Content: {r.entity.get('content', '')[:100]}...")

            return True

        except Exception as e:
            print(f"❌ Collection访问失败: {e}")
            return False

    except ImportError:
        print("⚠️ pymilvus 未安装，跳过Milvus测试")
        return False
    except Exception as e:
        print(f"❌ Milvus连接失败: {e}")
        return False


def main():
    print("开始检查所有数据库和服务...\n")

    results = {
        "MySQL": test_mysql(),
        "PostgreSQL": test_postgres(),
        "Neo4j": test_neo4j(),
        "KB Ingest": test_kb_ingest(),
        "Milvus": test_milvus()
    }

    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    for service, status in results.items():
        status_str = "✅ 正常" if status else "❌ 异常"
        print(f"{service:15} : {status_str}")

    print("\n检查完成！")


if __name__ == "__main__":
    main()
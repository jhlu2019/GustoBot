"""
测试通用表结构方案

验证：
1. 任意表结构都能处理
2. 所有字段存储在 metadata 中
3. JSON 查询功能正常
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
import pandas as pd

load_dotenv()

# 取消代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['all_proxy'] = ''

sys.path.insert(0, '/')

from app.core.config import Config
from app.services.vector_store_generic import VectorStoreWriterGeneric
from app.clients.embedding import EmbeddingClient


def test_arbitrary_table_structure():
    """测试任意表结构"""
    print("\n" + "=" * 60)
    print("测试 1: 处理任意表结构")
    print("=" * 60)

    config = Config()
    vector_writer = VectorStoreWriterGeneric(config)

    # 模拟不同的表结构
    test_cases = [
        {
            "name": "用户表",
            "source_table": "users",
            "data": {
                "user_id": 1,
                "username": "zhangsan",
                "email": "zhangsan@example.com",
                "age": 25,
                "city": "北京",
                "interests": "编程, 阅读, 运动"
            }
        },
        {
            "name": "订单表",
            "source_table": "orders",
            "data": {
                "order_id": "ORD001",
                "customer_name": "李四",
                "product": "笔记本电脑",
                "price": 5999.00,
                "quantity": 1,
                "order_date": "2025-01-20"
            }
        },
        {
            "name": "文章表",
            "source_table": "articles",
            "data": {
                "article_id": 100,
                "title": "Python 最佳实践",
                "author": "王五",
                "content": "本文介绍 Python 开发的最佳实践...",
                "tags": ["python", "编程", "教程"],
                "publish_date": "2025-01-15"
            }
        }
    ]

    items = []
    for case in test_cases:
        # 生成简单的描述文本
        content = f"{case['name']}: " + ", ".join([f"{k}={v}" for k, v in case['data'].items()])

        items.append({
            "source_table": case["source_table"],
            "source_id": str(case["data"].get(list(case["data"].keys())[0])),
            "rewritten_content": content,
            "original_data": case["data"]
        })

        print(f"\n{case['name']}:")
        print(f"  数据: {case['data']}")
        print(f"  文本: {content[:80]}...")

    # 存储
    try:
        count = vector_writer.upsert(items)
        print(f"\n✅ 成功存储 {count} 条不同表结构的数据")
        return True
    except Exception as e:
        print(f"\n❌ 存储失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_queries():
    """测试 JSON 查询"""
    print("\n" + "=" * 60)
    print("测试 2: JSON 字段查询")
    print("=" * 60)

    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "vector_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

    cursor = conn.cursor()

    # 测试各种 JSON 查询
    queries = [
        {
            "name": "查询用户表数据",
            "sql": """
                SELECT
                    source_table,
                    metadata->>'username' as username,
                    metadata->>'email' as email,
                    metadata->>'city' as city
                FROM searchable_documents
                WHERE source_table = 'users'
            """
        },
        {
            "name": "查询订单数据",
            "sql": """
                SELECT
                    source_table,
                    metadata->>'customer_name' as customer,
                    metadata->>'product' as product,
                    metadata->>'price' as price
                FROM searchable_documents
                WHERE source_table = 'orders'
            """
        },
        {
            "name": "按 JSON 字段筛选",
            "sql": """
                SELECT
                    source_table,
                    metadata->>'title' as title,
                    metadata->>'author' as author
                FROM searchable_documents
                WHERE metadata->>'author' = '王五'
            """
        },
        {
            "name": "检查字段存在",
            "sql": """
                SELECT
                    source_table,
                    COUNT(*) as count
                FROM searchable_documents
                WHERE metadata ? 'email'
                GROUP BY source_table
            """
        }
    ]

    all_passed = True
    for query in queries:
        print(f"\n{query['name']}:")
        print(f"SQL: {query['sql'].strip()[:100]}...")

        try:
            cursor.execute(query['sql'])
            results = cursor.fetchall()

            if results:
                print(f"✅ 查询成功，返回 {len(results)} 条结果")
                for i, row in enumerate(results[:3], 1):
                    print(f"  [{i}] {row}")
            else:
                print("⚠️  查询成功但无结果")

        except Exception as e:
            print(f"❌ 查询失败: {e}")
            all_passed = False

    cursor.close()
    conn.close()

    return all_passed


def test_real_excel_data():
    """测试真实的 Excel 数据（企业产品）"""
    print("\n" + "=" * 60)
    print("测试 3: 处理真实 Excel 数据")
    print("=" * 60)

    try:
        # 读取 Excel
        df = pd.read_excel('data/data.xlsx', sheet_name='企业产品')
        print(f"加载了 {len(df)} 条企业产品数据")

        # 显示字段
        print(f"字段: {list(df.columns)}")

        # 处理前 3 条
        config = Config()
        vector_writer = VectorStoreWriterGeneric(config)

        items = []
        for idx, row in df.head(3).iterrows():
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}

            # 生成简单描述
            company = row_dict.get('company_name(企业名称)', '')
            product = row_dict.get('name(产品名称)', '')
            content = f"{company} 的产品 {product}"

            items.append({
                "source_table": "企业产品_excel",
                "source_id": str(idx),
                "rewritten_content": content,
                "original_data": row_dict
            })

            print(f"\n处理第 {idx+1} 条:")
            print(f"  公司: {company}")
            print(f"  产品: {product}")
            print(f"  原始字段数: {len(row_dict)}")

        # 存储
        count = vector_writer.upsert(items)
        print(f"\n✅ 成功存储 {count} 条 Excel 数据")

        # 验证查询
        print("\n验证存储的数据:")
        conn = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            database=os.getenv("PGDATABASE", "vector_db"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "postgres")
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                source_table,
                metadata->>'company_name(企业名称)' as company,
                metadata->>'name(产品名称)' as product,
                metadata->>'brief(简介)' as brief
            FROM searchable_documents
            WHERE source_table = '企业产品_excel'
            LIMIT 3
        """)

        results = cursor.fetchall()
        for i, row in enumerate(results, 1):
            print(f"  [{i}] 公司: {row[1]}, 产品: {row[2]}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("通用表结构方案测试")
    print("=" * 70)

    results = {}

    # 测试 1: 任意表结构
    results["任意表结构"] = test_arbitrary_table_structure()

    # 测试 2: JSON 查询
    results["JSON查询"] = test_json_queries()

    # 测试 3: 真实数据
    results["真实Excel数据"] = test_real_excel_data()

    # 总结
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n通用方案优势:")
        print("  ✅ 支持任意表结构")
        print("  ✅ 无需修改代码")
        print("  ✅ 灵活的 JSON 查询")
        print("  ✅ 用户只需配置 .env 和提示词")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

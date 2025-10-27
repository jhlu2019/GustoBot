"""端到端测试：LLM重写 → Embedding → 存储 → 检索 → Rerank"""
import os
import sys
from dotenv import load_dotenv
import pandas as pd
import psycopg2

load_dotenv()

# 取消代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['all_proxy'] = ''

sys.path.insert(0, '/')

from app.clients.llm import LLMClient
from app.clients.embedding import EmbeddingClient
from app.core.config import Config
from app.prompts.manager import PromptManager, SchemaColumn
from app.services.vector_store import VectorStoreWriter


def create_test_table():
    """创建测试专用表"""
    print("\n" + "="*60)
    print("步骤 1: 创建测试表")
    print("="*60)

    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "vector_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

    cursor = conn.cursor()

    # 删除旧的测试表
    cursor.execute("DROP TABLE IF EXISTS test_products_llm")

    # 创建新的测试表
    cursor.execute("""
        CREATE TABLE test_products_llm (
            id SERIAL PRIMARY KEY,
            source_table TEXT,
            source_id TEXT,
            content TEXT,
            embedding vector(1024),
            company_name TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_table, source_id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ 测试表 test_products_llm 创建成功")


def load_and_rewrite_data():
    """加载数据并使用LLM重写"""
    print("\n" + "="*60)
    print("步骤 2: 加载数据并使用 LLM 重写")
    print("="*60)

    # 加载数据
    df = pd.read_excel('data/data.xlsx', sheet_name='企业产品')
    print(f"加载了 {len(df)} 条企业产品数据")

    # 初始化服务
    config = Config()
    llm_client = LLMClient(config)
    embedding_client = EmbeddingClient(config)
    prompt_manager = PromptManager()

    # 处理每条数据
    results = []

    for idx, row in df.iterrows():
        print(f"\n处理第 {idx+1}/{len(df)} 条数据...")

        # 转换为字典
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}

        # 提取公司名称
        company_name = row_dict.get('company_name(企业名称)', '')
        product_name = row_dict.get('name(产品名称)', '')

        print(f"  公司: {company_name}")
        print(f"  产品: {product_name}")

        # 定义 schema
        schema = [
            SchemaColumn(name="company_name(企业名称)", data_type="varchar", comment="企业名称"),
            SchemaColumn(name="name(产品名称)", data_type="varchar", comment="产品名称"),
            SchemaColumn(name="intro(介绍)", data_type="text", comment="产品介绍"),
            SchemaColumn(name="brief(简介)", data_type="text", comment="产品简介"),
            SchemaColumn(name="status(运营状态)", data_type="varchar", comment="运营状态"),
            SchemaColumn(name="website(项目地址)", data_type="varchar", comment="网站地址"),
        ]

        # 使用 LLM 重写
        try:
            system_prompt, user_prompt = prompt_manager.get_prompt(
                table_name="企业产品",
                row_data=row_dict,
                schema=schema,
            )

            print("  调用 LLM 重写...")
            rewritten_content = llm_client.generate(user_prompt, system_prompt)
            print(f"  ✅ 重写完成 (长度: {len(rewritten_content)})")
            print(f"  重写内容: {rewritten_content[:100]}...")

            # 生成 embedding
            print("  生成 embedding...")
            embeddings = embedding_client.embed_texts([rewritten_content])
            embedding = embeddings[0].tolist()  # 转换为列表
            print(f"  ✅ Embedding 生成完成 (维度: {len(embedding)})")

            results.append({
                'source_id': str(idx),
                'company_name': company_name,
                'content': rewritten_content,
                'embedding': embedding,
                'original_data': row_dict
            })

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            continue

    print(f"\n✅ 成功处理 {len(results)} 条数据")
    return results


def store_to_database(results):
    """存储到数据库"""
    print("\n" + "="*60)
    print("步骤 3: 存储到 PostgreSQL")
    print("="*60)

    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "vector_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

    cursor = conn.cursor()

    for item in results:
        cursor.execute("""
            INSERT INTO test_products_llm
                (source_table, source_id, content, embedding, company_name, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_table, source_id)
            DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                company_name = EXCLUDED.company_name,
                metadata = EXCLUDED.metadata
        """, (
            '企业产品',
            item['source_id'],
            item['content'],
            item['embedding'],
            item['company_name'],
            str(item['original_data'])
        ))

    conn.commit()

    # 验证
    cursor.execute("SELECT COUNT(*) FROM test_products_llm")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"✅ 成功存储 {count} 条数据到 test_products_llm 表")


def test_vector_search(query: str):
    """测试向量检索"""
    print("\n" + "="*60)
    print(f"步骤 4: 向量检索测试")
    print("="*60)
    print(f"查询: {query}")

    # 生成查询的 embedding
    config = Config()
    embedding_client = EmbeddingClient(config)

    print("生成查询向量...")
    query_embeddings = embedding_client.embed_texts([query])
    query_embedding = query_embeddings[0].tolist()
    print(f"✅ 查询向量生成完成 (维度: {len(query_embedding)})")

    # 向量检索
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "vector_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

    cursor = conn.cursor()

    # 使用余弦相似度检索
    cursor.execute("""
        SELECT
            id,
            company_name,
            content,
            1 - (embedding <=> %s::vector) as similarity
        FROM test_products_llm
        ORDER BY embedding <=> %s::vector
        LIMIT 10
    """, (query_embedding, query_embedding))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"\n✅ 检索到 {len(results)} 条结果")
    print("\n向量检索结果 (Top 5):")
    print("-" * 60)

    for i, (id, company_name, content, similarity) in enumerate(results[:5], 1):
        print(f"\n[{i}] 相似度: {similarity:.4f}")
        print(f"    公司: {company_name}")
        print(f"    内容: {content[:100]}...")

    return results


def test_rerank(query: str, search_results):
    """测试 Rerank 重排序"""
    print("\n" + "="*60)
    print("步骤 5: Rerank 重排序测试")
    print("="*60)

    import requests

    # 准备文档列表
    documents = [result[2] for result in search_results[:10]]  # content

    print(f"查询: {query}")
    print(f"候选文档数: {len(documents)}")

    # 调用 Rerank API
    try:
        response = requests.post(
            "http://10.168.2.110:9997/v1/rerank",
            headers={
                "Authorization": f"Bearer {os.getenv('RERANK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "bge-reranker-large",
                "query": query,
                "documents": documents,
                "top_n": 5
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("\n✅ Rerank 成功")
            print("\nRerank 后的结果 (Top 5):")
            print("-" * 60)

            for i, item in enumerate(result['results'][:5], 1):
                idx = item['index']
                score = item['relevance_score']
                original_result = search_results[idx]

                print(f"\n[{i}] Rerank Score: {score:.4f}")
                print(f"    原始排名: #{idx+1}")
                print(f"    向量相似度: {original_result[3]:.4f}")
                print(f"    公司: {original_result[1]}")
                print(f"    内容: {original_result[2][:100]}...")

            return True
        else:
            print(f"❌ Rerank 失败: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Rerank 调用失败: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "="*70)
    print("端到端测试：LLM重写 → Embedding → 存储 → 检索 → Rerank")
    print("="*70)

    try:
        # 1. 创建测试表
        create_test_table()

        # 2. 加载数据并使用 LLM 重写
        results = load_and_rewrite_data()

        if not results:
            print("❌ 没有数据可处理")
            return False

        # 3. 存储到数据库
        store_to_database(results)

        # 4. 测试向量检索
        test_query = "智能制造和工厂自动化解决方案"
        search_results = test_vector_search(test_query)

        # 5. 测试 Rerank
        test_rerank(test_query, search_results)

        print("\n" + "="*70)
        print("✅ 端到端测试完成！")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

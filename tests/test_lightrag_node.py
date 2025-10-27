"""
测试 LightRAG Node 的初始化和基本功能
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入必要的模块
from app.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI
from app.core.logger import get_logger

logger = get_logger(service="test-lightrag")


async def test_initialization():
    """测试 LightRAG 初始化"""
    logger.info("=" * 50)
    logger.info("测试 LightRAG 初始化")
    logger.info("=" * 50)

    try:
        # 创建 LightRAG API 实例
        lightrag_api = LightRAGAPI(
            working_dir="./test_lightrag_data",
            retrieval_mode="hybrid",
            top_k=5,
            enable_neo4j=False  # 先测试不使用 Neo4j
        )

        # 初始化
        logger.info("开始初始化 LightRAG...")
        await lightrag_api.initialize()
        logger.info("✓ LightRAG 初始化成功")

        return lightrag_api

    except Exception as e:
        logger.error(f"✗ 初始化失败: {str(e)}", exc_info=True)
        raise


async def test_embedding():
    """测试 Embedding 函数"""
    logger.info("\n" + "=" * 50)
    logger.info("测试 Embedding 函数")
    logger.info("=" * 50)

    try:
        lightrag_api = await test_initialization()

        # 测试 embedding
        test_texts = ["这是一个测试文本", "红烧肉的做法", "如何制作宫保鸡丁"]
        logger.info(f"测试文本: {test_texts}")

        embeddings = await lightrag_api.rag.embedding_func(test_texts)
        logger.info(f"✓ Embedding 成功")
        logger.info(f"  - 向量维度: {len(embeddings[0])}")
        logger.info(f"  - 向量数量: {len(embeddings)}")

    except Exception as e:
        logger.error(f"✗ Embedding 测试失败: {str(e)}", exc_info=True)
        raise


async def test_insert_document():
    """测试插入文档"""
    logger.info("\n" + "=" * 50)
    logger.info("测试插入文档")
    logger.info("=" * 50)

    try:
        lightrag_api = await test_initialization()

        # 测试文档
        test_doc = """
        红烧肉是一道经典的中华料理，以五花肉为主要食材。

        主要食材：
        - 五花肉 500克
        - 冰糖 30克
        - 生抽 2勺
        - 老抽 1勺
        - 料酒 2勺

        制作步骤：
        1. 将五花肉切成2厘米见方的块状
        2. 冷水下锅，焯水去除血沫
        3. 锅中放少许油，放入冰糖炒糖色
        4. 加入五花肉翻炒上色
        5. 加入生抽、老抽、料酒
        6. 加水没过肉，大火烧开后转小火炖1小时
        7. 大火收汁即可

        烹饪技巧：
        - 糖色不要炒过头，否则会发苦
        - 炖煮时间要足够，肉质才会软烂
        - 最后收汁要用大火，让汁水浓稠
        """

        logger.info("插入测试文档...")
        result = await lightrag_api.insert_documents([test_doc])
        logger.info(f"✓ 文档插入成功")
        logger.info(f"  - 成功: {result['success']}")
        logger.info(f"  - 失败: {result['error']}")

    except Exception as e:
        logger.error(f"✗ 文档插入失败: {str(e)}", exc_info=True)
        raise


async def test_query():
    """测试查询功能"""
    logger.info("\n" + "=" * 50)
    logger.info("测试查询功能")
    logger.info("=" * 50)

    try:
        # 先插入文档
        await test_insert_document()

        # 创建新的 API 实例进行查询
        lightrag_api = LightRAGAPI(
            working_dir="./test_lightrag_data",
            retrieval_mode="hybrid",
            top_k=5,
            enable_neo4j=False
        )
        await lightrag_api.initialize()

        # 测试查询
        query = "红烧肉怎么做？"
        logger.info(f"查询: {query}")

        result = await lightrag_api.query(query, mode="hybrid")
        logger.info(f"✓ 查询成功")
        logger.info(f"  - 查询模式: {result['mode']}")
        logger.info(f"  - 响应长度: {len(result['response'])} 字符")
        logger.info(f"\n响应内容:\n{result['response'][:500]}...")

    except Exception as e:
        logger.error(f"✗ 查询失败: {str(e)}", exc_info=True)
        raise


async def test_with_neo4j():
    """测试 Neo4j 集成"""
    logger.info("\n" + "=" * 50)
    logger.info("测试 Neo4j 集成")
    logger.info("=" * 50)

    try:
        # 创建使用 Neo4j 的实例
        lightrag_api = LightRAGAPI(
            working_dir="./test_lightrag_neo4j",
            retrieval_mode="hybrid",
            top_k=5,
            enable_neo4j=True
        )

        logger.info("初始化 LightRAG (使用 Neo4j)...")
        await lightrag_api.initialize()
        logger.info("✓ 使用 Neo4j 的 LightRAG 初始化成功")

    except Exception as e:
        logger.error(f"✗ Neo4j 集成测试失败 (这是正常的，如果 Neo4j 未运行): {str(e)}")
        logger.info("跳过 Neo4j 测试...")


async def main():
    """运行所有测试"""
    logger.info("开始测试 LightRAG Node 实现\n")

    try:
        # 测试 1: 初始化
        await test_initialization()

        # 测试 2: Embedding
        await test_embedding()

        # 测试 3: 插入文档和查询
        await test_query()

        # 测试 4: Neo4j 集成 (可选)
        await test_with_neo4j()

        logger.info("\n" + "=" * 50)
        logger.info("✓ 所有测试完成")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"\n✗ 测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

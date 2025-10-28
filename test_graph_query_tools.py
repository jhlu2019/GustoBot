#!/usr/bin/env python3
"""
测试 Graph Query 工具的脚本
测试项目中的不同 graph-query 工具（cypher_query, predefined_cypher, microsoft_graphrag_query, text2sql_query）
"""
import asyncio
import json
from typing import Any, Dict
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


async def test_neo4j_connection():
    """测试 Neo4j 连接"""
    logger.info("=" * 80)
    logger.info("测试 1: Neo4j 连接测试")
    logger.info("=" * 80)

    try:
        from app.knowledge_base.recipe_kg.graph_database_client import Neo4jDatabase
        from app.config import settings

        db = Neo4jDatabase(
            settings.NEO4J_URI,
            settings.NEO4J_USER,
            settings.NEO4J_PASSWORD,
        )

        # 测试简单查询
        result = db.fetch("MATCH (d:Dish) RETURN count(d) as dish_count LIMIT 1", {})
        logger.success(f"✓ Neo4j 连接成功！菜品数量: {result}")
        db.close()
        return True

    except Exception as e:
        logger.error(f"✗ Neo4j 连接失败: {e}")
        return False


async def test_neo4j_qa_service():
    """测试 Neo4j QA Service (包含预定义 Cypher 和问题分类)"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 2: Neo4j QA Service 测试")
    logger.info("=" * 80)

    try:
        from app.knowledge_base.recipe_kg.neo4j_qa_service import Neo4jQAService

        service = Neo4jQAService()

        # 测试问题列表
        test_questions = [
            "红烧肉的做法是什么？",
            "有哪些麻辣口味的菜？",
            "五花肉可以做什么菜？",
            "红烧肉需要多少五花肉？",
        ]

        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n问题 {i}: {question}")
            try:
                result = service.ask(question)
                logger.success(f"  类型: {result.get('question_type', 'unknown')}")
                logger.success(f"  答案: {result.get('answer', 'N/A')[:200]}")
                if result.get('cypher'):
                    logger.info(f"  Cypher: {result['cypher'][0] if isinstance(result['cypher'], list) else result['cypher']}")
            except Exception as e:
                logger.error(f"  ✗ 查询失败: {e}")

        service.close()
        return True

    except Exception as e:
        logger.error(f"✗ Neo4j QA Service 测试失败: {e}")
        return False


async def test_text2cypher_tool():
    """测试 Text2Cypher 工具"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 3: Text2Cypher 工具测试")
    logger.info("=" * 80)

    try:
        from app.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.text2sql_tool import (
            Text2CypherTool,
        )
        from app.knowledge_base.recipe_kg.graph_database_client import Neo4jDatabase
        from app.config import settings

        db = Neo4jDatabase(
            settings.NEO4J_URI,
            settings.NEO4J_USER,
            settings.NEO4J_PASSWORD,
        )

        tool = Text2CypherTool(db)

        test_questions = [
            "查询所有川菜菜品",
            "找出使用五花肉的菜品",
            "列出所有麻辣口味的菜",
        ]

        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n问题 {i}: {question}")
            try:
                result = await tool.run(question)
                logger.success(f"  结果: {str(result)[:200]}")
            except Exception as e:
                logger.error(f"  ✗ 查询失败: {e}")

        db.close()
        return True

    except Exception as e:
        logger.error(f"✗ Text2Cypher 工具测试失败: {e}")
        logger.exception(e)
        return False


async def test_predefined_cypher_queries():
    """测试预定义 Cypher 查询"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 4: 预定义 Cypher 查询测试")
    logger.info("=" * 80)

    try:
        from app.agents.kg_sub_graph.agentic_rag_agents.components.predefined_cypher.cypher_dict import (
            CYPHER_QUERIES,
        )
        from app.knowledge_base.recipe_kg.graph_database_client import Neo4jDatabase
        from app.config import settings

        db = Neo4jDatabase(
            settings.NEO4J_URI,
            settings.NEO4J_USER,
            settings.NEO4J_PASSWORD,
        )

        # 显示可用的预定义查询
        logger.info(f"可用的预定义查询数量: {len(CYPHER_QUERIES)}")
        logger.info(f"查询列表: {', '.join(list(CYPHER_QUERIES.keys())[:10])}...")

        # 测试几个预定义查询
        test_cases = [
            {
                "query_name": "dishes_by_flavor",
                "params": {"flavor_name": "麻辣"},
                "description": "查询麻辣口味的菜品",
            },
            {
                "query_name": "dishes_by_main_ingredient",
                "params": {"ingredient_name": "五花肉"},
                "description": "查询使用五花肉的菜品",
            },
            {
                "query_name": "cooking_steps",
                "params": {"dish_name": "红烧肉"},
                "description": "查询红烧肉的烹饪步骤",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            query_name = test_case["query_name"]
            params = test_case["params"]
            description = test_case["description"]

            logger.info(f"\n测试 {i}: {description}")
            logger.info(f"  查询名称: {query_name}")
            logger.info(f"  参数: {params}")

            if query_name in CYPHER_QUERIES:
                cypher_template = CYPHER_QUERIES[query_name]
                logger.info(f"  Cypher 模板: {cypher_template[:100]}...")

                try:
                    result = db.fetch(cypher_template, params)
                    logger.success(f"  ✓ 查询成功！结果数量: {len(result)}")
                    if result:
                        logger.info(f"  示例结果: {result[0]}")
                except Exception as e:
                    logger.error(f"  ✗ 查询执行失败: {e}")
            else:
                logger.error(f"  ✗ 查询 '{query_name}' 不存在")

        db.close()
        return True

    except Exception as e:
        logger.error(f"✗ 预定义 Cypher 查询测试失败: {e}")
        logger.exception(e)
        return False


async def test_tool_selection():
    """测试工具选择逻辑"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 5: 工具选择逻辑测试")
    logger.info("=" * 80)

    try:
        from app.agents.kg_sub_graph.kg_tools_list import (
            cypher_query,
            predefined_cypher,
            microsoft_graphrag_query,
            text2sql_query,
        )

        # 显示工具定义
        tools = [cypher_query, predefined_cypher, microsoft_graphrag_query, text2sql_query]

        for i, tool_class in enumerate(tools, 1):
            schema = tool_class.model_json_schema()
            logger.info(f"\n工具 {i}: {schema.get('title', 'Unknown')}")
            logger.info(f"  描述: {schema.get('description', 'N/A')[:100]}...")
            logger.info(f"  字段: {list(schema.get('properties', {}).keys())}")

        return True

    except Exception as e:
        logger.error(f"✗ 工具选择测试失败: {e}")
        logger.exception(e)
        return False


async def test_graphrag_availability():
    """测试 GraphRAG 可用性"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 6: GraphRAG 可用性测试")
    logger.info("=" * 80)

    try:
        # 检查 LightRAG 数据目录
        import os
        from pathlib import Path

        lightrag_dir = Path("data/lightrag")
        logger.info(f"检查 LightRAG 数据目录: {lightrag_dir}")

        if lightrag_dir.exists():
            files = list(lightrag_dir.glob("*"))
            logger.success(f"✓ LightRAG 数据目录存在，包含 {len(files)} 个文件")
            for f in files[:5]:
                logger.info(f"  - {f.name}")
        else:
            logger.warning(f"⚠ LightRAG 数据目录不存在，GraphRAG 可能未初始化")

        # 尝试导入 GraphRAG 相关模块
        try:
            from app.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import (
                create_customer_tools_node,
            )
            logger.success("✓ GraphRAG 相关模块导入成功")
        except ImportError as e:
            logger.warning(f"⚠ GraphRAG 模块导入失败: {e}")

        return True

    except Exception as e:
        logger.error(f"✗ GraphRAG 可用性测试失败: {e}")
        logger.exception(e)
        return False


async def main():
    """主测试函数"""
    logger.info("开始测试 Graph Query 工具...")
    logger.info("=" * 80)

    results = {}

    # 运行所有测试
    tests = [
        ("Neo4j 连接", test_neo4j_connection),
        ("Neo4j QA Service", test_neo4j_qa_service),
        ("Text2Cypher 工具", test_text2cypher_tool),
        ("预定义 Cypher 查询", test_predefined_cypher_queries),
        ("工具选择逻辑", test_tool_selection),
        ("GraphRAG 可用性", test_graphrag_availability),
    ]

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = "✓ 通过" if result else "✗ 失败"
        except Exception as e:
            logger.error(f"测试 '{test_name}' 发生异常: {e}")
            results[test_name] = f"✗ 异常: {str(e)[:50]}"

    # 输出测试总结
    logger.info("\n" + "=" * 80)
    logger.info("测试总结")
    logger.info("=" * 80)

    for test_name, result in results.items():
        status_symbol = "✓" if "✓" in result else "✗"
        logger.info(f"{status_symbol} {test_name}: {result}")

    passed = sum(1 for r in results.values() if "✓" in r)
    total = len(results)
    logger.info(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())

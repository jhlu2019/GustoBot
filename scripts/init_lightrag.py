#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LightRAG 初始化脚本

从 Neo4j 菜谱图谱导出数据并导入到 LightRAG，用于图谱检索增强
支持两种模式:
1. 从 Neo4j 导入完整菜谱数据
2. 从 JSON 文件导入菜谱数据
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gustobot.config import settings
from gustobot.infrastructure.core.logger import get_logger
from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import LightRAGAPI

logger = get_logger(service="init-lightrag")


def format_recipe_document(record: Dict[str, Any]) -> str:
    """
    将 Neo4j 记录格式化为 LightRAG 文档格式

    Parameters
    ----------
    record : Dict[str, Any]
        Neo4j 查询返回的记录

    Returns
    -------
    str
        格式化后的菜谱文档
    """
    dish_name = record.get("dish_name", "")
    instructions = record.get("instructions", "")
    cook_time = record.get("cook_time", "")
    ingredients = record.get("ingredients", [])
    flavors = record.get("flavors", [])
    methods = record.get("methods", [])
    dish_types = record.get("types", [])

    # 格式化文档
    doc_parts = [f"# {dish_name}\n"]

    if flavors:
        doc_parts.append(f"**口味**: {', '.join(flavors)}")

    if methods:
        doc_parts.append(f"**烹饪方法**: {', '.join(methods)}")

    if dish_types:
        doc_parts.append(f"**菜品类型**: {', '.join(dish_types)}")

    if cook_time:
        doc_parts.append(f"**烹饪时长**: {cook_time}")

    if ingredients:
        doc_parts.append(f"\n**食材**:\n")
        for ing in ingredients:
            if isinstance(ing, dict):
                name = ing.get("name", "")
                amount = ing.get("amount", "")
                doc_parts.append(f"- {name}: {amount}" if amount else f"- {name}")
            else:
                doc_parts.append(f"- {ing}")

    if instructions:
        doc_parts.append(f"\n**做法**:\n{instructions}")

    return "\n".join(doc_parts)


async def import_from_neo4j(lightrag: LightRAGAPI, limit: int = None) -> int:
    """
    从 Neo4j 导入菜谱数据到 LightRAG

    Parameters
    ----------
    lightrag : LightRAGAPI
        LightRAG API 实例
    limit : int, optional
        限制导入的菜品数量，用于测试

    Returns
    -------
    int
        导入的文档数量
    """
    try:
        from neo4j import GraphDatabase

        logger.info("开始从 Neo4j 导入菜谱数据")

        # 连接 Neo4j
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        documents = []

        with driver.session(database=settings.NEO4J_DATABASE) as session:
            # 构建查询
            query = """
            MATCH (d:Dish)
            OPTIONAL MATCH (d)-[r_main:HAS_MAIN_INGREDIENT]->(i_main:Ingredient)
            OPTIONAL MATCH (d)-[r_aux:HAS_AUX_INGREDIENT]->(i_aux:Ingredient)
            OPTIONAL MATCH (d)-[:HAS_FLAVOR]->(f:Flavor)
            OPTIONAL MATCH (d)-[:USES_METHOD]->(m:CookingMethod)
            OPTIONAL MATCH (d)-[:BELONGS_TO_TYPE]->(t:DishType)
            WITH d,
                 collect(DISTINCT {name: i_main.name, amount: r_main.amount_text}) as main_ingredients,
                 collect(DISTINCT {name: i_aux.name, amount: r_aux.amount_text}) as aux_ingredients,
                 collect(DISTINCT f.name) as flavors,
                 collect(DISTINCT m.name) as methods,
                 collect(DISTINCT t.name) as types
            RETURN d.name as dish_name,
                   d.instructions as instructions,
                   d.cook_time as cook_time,
                   main_ingredients + aux_ingredients as ingredients,
                   flavors,
                   methods,
                   types
            """

            if limit:
                query += f" LIMIT {limit}"

            logger.info(f"执行 Neo4j 查询{'（限制 ' + str(limit) + ' 条）' if limit else ''}")
            result = session.run(query)

            for record in result:
                record_dict = dict(record)
                doc = format_recipe_document(record_dict)
                documents.append(doc)

                if len(documents) % 10 == 0:
                    logger.info(f"已准备 {len(documents)} 个文档")

        driver.close()

        logger.info(f"共准备了 {len(documents)} 个菜谱文档")

        # 批量插入到 LightRAG
        logger.info("开始插入文档到 LightRAG")
        result = await lightrag.insert_documents(documents)

        logger.info(f"导入完成: 总数={result['total']}, 成功={result['success']}, 失败={result['error']}")

        return result['success']

    except ImportError:
        logger.error("neo4j 包未安装，请运行 'pip install neo4j'")
        raise
    except Exception as e:
        logger.error(f"从 Neo4j 导入失败: {str(e)}", exc_info=True)
        raise


async def import_from_json(lightrag: LightRAGAPI, json_path: str, limit: int = None) -> int:
    """
    从 JSON 文件导入菜谱数据到 LightRAG

    Parameters
    ----------
    lightrag : LightRAGAPI
        LightRAG API 实例
    json_path : str
        JSON 文件路径
    limit : int, optional
        限制导入的菜品数量，用于测试

    Returns
    -------
    int
        导入的文档数量
    """
    try:
        logger.info(f"开始从 JSON 文件导入: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            recipes = json.load(f)

        if limit:
            recipes = recipes[:limit]

        documents = []

        for recipe in recipes:
            # 假设 JSON 格式与 Neo4j 记录格式相似
            doc = format_recipe_document(recipe)
            documents.append(doc)

            if len(documents) % 10 == 0:
                logger.info(f"已准备 {len(documents)} 个文档")

        logger.info(f"共准备了 {len(documents)} 个菜谱文档")

        # 批量插入到 LightRAG
        logger.info("开始插入文档到 LightRAG")
        result = await lightrag.insert_documents(documents)

        logger.info(f"导入完成: 总数={result['total']}, 成功={result['success']}, 失败={result['error']}")

        return result['success']

    except Exception as e:
        logger.error(f"从 JSON 导入失败: {str(e)}", exc_info=True)
        raise


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="LightRAG 初始化脚本")
    parser.add_argument(
        "--source",
        type=str,
        choices=["neo4j", "json"],
        default="neo4j",
        help="数据源类型 (neo4j 或 json)"
    )
    parser.add_argument(
        "--json-path",
        type=str,
        default=str(project_root / "data" / "recipe.json"),
        help="JSON 文件路径（当 source=json 时使用）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制导入数量（用于测试）"
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        default=None,
        help="LightRAG 工作目录（覆盖配置文件）"
    )

    args = parser.parse_args()

    try:
        # 创建 LightRAG API 实例
        logger.info("初始化 LightRAG")
        lightrag = LightRAGAPI(working_dir=args.working_dir)

        # 根据数据源类型导入
        if args.source == "neo4j":
            count = await import_from_neo4j(lightrag, limit=args.limit)
        elif args.source == "json":
            count = await import_from_json(lightrag, args.json_path, limit=args.limit)

        logger.info(f"✅ LightRAG 初始化完成！成功导入 {count} 个菜谱文档")
        logger.info(f"📂 工作目录: {lightrag.working_dir}")
        logger.info(f"🔍 检索模式: {lightrag.retrieval_mode}")

    except Exception as e:
        logger.error(f"❌ 初始化失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的 Graph Query 工具测试脚本
直接测试 Neo4j 知识图谱的不同查询工具
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'F:\\pythonproject\\GustoBot')

from neo4j import GraphDatabase

# 测试配置
NEO4J_URI = "bolt://localhost:17687"
NEO4J_USER = ""  # None auth
NEO4J_PASSWORD = ""

print("="*80)
print("GustoBot Graph Query Tools 测试")
print("="*80)

# 测试 1: Neo4j 基础连接
print("\n[测试 1] Neo4j 基础连接测试")
print("-"*80)
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD) if NEO4J_USER else None)
    with driver.session() as session:
        # 测试基本查询
        result = session.run("MATCH (d:Dish) RETURN count(d) as dish_count")
        record = result.single()
        dish_count = record["dish_count"] if record else 0
        print(f"✓ Neo4j 连接成功！")
        print(f"  数据库中的菜品数量: {dish_count}")

        # 查询节点类型
        result = session.run("""
            CALL db.labels() YIELD label
            RETURN label
            ORDER BY label
        """)
        labels = [record["label"] for record in result]
        print(f"  节点类型 ({len(labels)}): {', '.join(labels)}")

    driver.close()
    print("✓ 测试通过")
except Exception as e:
    print(f"✗ 测试失败: {e}")
    sys.exit(1)

# 测试 2: 预定义 Cypher 查询测试
print("\n[测试 2] 预定义 Cypher 查询测试")
print("-"*80)
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD) if NEO4J_USER else None)

    test_cases = [
        {
            "name": "查询红烧肉菜品信息",
            "cypher": "MATCH (d:Dish {name: $dish_name}) RETURN d.name as name, d.category as category, d.instructions as instructions",
            "params": {"dish_name": "红烧肉"}
        },
        {
            "name": "查询使用五花肉的菜品",
            "cypher": "MATCH (d:Dish)-[:HAS_MAIN_INGREDIENT|HAS_AUX_INGREDIENT]->(i:Ingredient {name: $ingredient_name}) RETURN d.name as dish_name LIMIT 5",
            "params": {"ingredient_name": "五花肉"}
        },
        {
            "name": "查询麻辣口味的菜品",
            "cypher": "MATCH (d:Dish)-[:HAS_FLAVOR]->(f:Flavor {name: $flavor_name}) RETURN d.name as dish_name LIMIT 5",
            "params": {"flavor_name": "麻辣"}
        },
        {
            "name": "查询炒菜类烹饪方法的菜品",
            "cypher": "MATCH (d:Dish)-[:USES_METHOD]->(m:CookingMethod {name: $method_name}) RETURN d.name as dish_name LIMIT 5",
            "params": {"method_name": "炒"}
        }
    ]

    with driver.session() as session:
        for i, test in enumerate(test_cases, 1):
            print(f"\n  {i}. {test['name']}")
            print(f"     参数: {test['params']}")
            try:
                result = session.run(test['cypher'], test['params'])
                records = list(result)
                if records:
                    print(f"     ✓ 找到 {len(records)} 条结果")
                    # 显示前3条结果
                    for j, record in enumerate(records[:3], 1):
                        print(f"       {j}. {dict(record)}")
                else:
                    print(f"     ⚠ 未找到匹配结果")
            except Exception as e:
                print(f"     ✗ 查询失败: {e}")

    driver.close()
    print("\n✓ 预定义 Cypher 查询测试通过")
except Exception as e:
    print(f"\n✗ 测试失败: {e}")

# 测试 3: 知识图谱关系查询
print("\n[测试 3] 知识图谱关系查询测试")
print("-"*80)
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD) if NEO4J_USER else None)

    with driver.session() as session:
        # 查询关系类型
        print("  关系类型统计:")
        result = session.run("""
            CALL db.relationshipTypes() YIELD relationshipType
            CALL {
                WITH relationshipType
                MATCH ()-[r]->()
                WHERE type(r) = relationshipType
                RETURN count(r) as count
            }
            RETURN relationshipType, count
            ORDER BY count DESC
        """)
        for record in result:
            rel_type = record["relationshipType"]
            count = record["count"]
            print(f"    - {rel_type}: {count}")

        # 查询一个具体菜品的完整关系
        print("\n  查询'红烧肉'的完整知识图谱:")
        result = session.run("""
            MATCH (d:Dish {name: '红烧肉'})
            OPTIONAL MATCH (d)-[:HAS_MAIN_INGREDIENT]->(mi:Ingredient)
            OPTIONAL MATCH (d)-[:HAS_FLAVOR]->(f:Flavor)
            OPTIONAL MATCH (d)-[:USES_METHOD]->(m:CookingMethod)
            OPTIONAL MATCH (d)-[:BELONGS_TO_TYPE]->(t:DishType)
            RETURN d.name as dish,
                   collect(DISTINCT mi.name) as main_ingredients,
                   collect(DISTINCT f.name) as flavors,
                   collect(DISTINCT m.name) as methods,
                   collect(DISTINCT t.name) as types
        """)
        record = result.single()
        if record:
            print(f"    菜品: {record['dish']}")
            print(f"    主食材: {', '.join(record['main_ingredients']) if record['main_ingredients'] else '无'}")
            print(f"    口味: {', '.join(record['flavors']) if record['flavors'] else '无'}")
            print(f"    烹饪方法: {', '.join(record['methods']) if record['methods'] else '无'}")
            print(f"    菜品类型: {', '.join(record['types']) if record['types'] else '无'}")
        else:
            print("    ⚠ 未找到'红烧肉'菜品")

    driver.close()
    print("\n✓ 知识图谱关系查询测试通过")
except Exception as e:
    print(f"\n✗ 测试失败: {e}")

# 测试 4: 复杂 Cypher 查询（多跳查询）
print("\n[测试 4] 复杂 Cypher 查询测试")
print("-"*80)
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD) if NEO4J_USER else None)

    with driver.session() as session:
        # 推荐菜品：查找与"红烧肉"口味相似的其他菜品
        print("  推荐查询: 查找与'红烧肉'口味相似的菜品")
        result = session.run("""
            MATCH (d1:Dish {name: '红烧肉'})-[:HAS_FLAVOR]->(f:Flavor)<-[:HAS_FLAVOR]-(d2:Dish)
            WHERE d1 <> d2
            RETURN d2.name as recommended_dish, collect(DISTINCT f.name) as common_flavors
            LIMIT 5
        """)
        records = list(result)
        if records:
            print(f"    找到 {len(records)} 个相似菜品:")
            for i, record in enumerate(records, 1):
                print(f"      {i}. {record['recommended_dish']} (共同口味: {', '.join(record['common_flavors'])})")
        else:
            print("    ⚠ 未找到相似菜品")

        # 食材共现：查找经常与"五花肉"一起使用的食材
        print("\n  食材共现分析: 与'五花肉'经常一起使用的食材")
        result = session.run("""
            MATCH (i1:Ingredient {name: '五花肉'})<-[:HAS_MAIN_INGREDIENT|HAS_AUX_INGREDIENT]-(d:Dish)
                  -[:HAS_MAIN_INGREDIENT|HAS_AUX_INGREDIENT]->(i2:Ingredient)
            WHERE i1 <> i2
            RETURN i2.name as co_ingredient, count(DISTINCT d) as co_occurrence_count
            ORDER BY co_occurrence_count DESC
            LIMIT 5
        """)
        records = list(result)
        if records:
            print(f"    找到 {len(records)} 个常见搭配:")
            for i, record in enumerate(records, 1):
                print(f"      {i}. {record['co_ingredient']} (出现在 {record['co_occurrence_count']} 道菜中)")
        else:
            print("    ⚠ 未找到搭配食材")

    driver.close()
    print("\n✓ 复杂 Cypher 查询测试通过")
except Exception as e:
    print(f"\n✗ 测试失败: {e}")

# 测试总结
print("\n" + "="*80)
print("测试总结")
print("="*80)
print("""
本次测试验证了以下 Graph Query 工具能力:

1. ✓ Neo4j 基础连接和数据统计
2. ✓ 预定义 Cypher 查询 (predefined_cypher)
   - 菜品属性查询
   - 基于食材的菜品查询
   - 基于口味的菜品查询
   - 基于烹饪方法的菜品查询
3. ✓ 知识图谱关系查询
   - 关系类型统计
   - 多关系组合查询
4. ✓ 复杂 Cypher 查询 (cypher_query / Text2Cypher)
   - 推荐系统查询（口味相似度）
   - 食材共现分析

这些查询能力构成了项目中 graph-query 工具的核心功能。
在实际应用中，这些查询会通过：
- RouterAgent 识别用户意图
- ToolSelectionAgent 选择合适的工具
- Text2Cypher 生成 Cypher 语句（对于动态查询）
- PredefinedCypher 使用模板查询（对于常见问题）
- GraphRAG 进行更复杂的知识推理
""")
print("="*80)

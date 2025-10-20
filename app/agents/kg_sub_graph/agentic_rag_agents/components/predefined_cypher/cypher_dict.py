"""
预定义菜谱 Cypher 查询字典
基于 recipe_kg 模块的 4 种问题类型和 Neo4j 菜谱图谱 schema 设计
对应 kg_tools_list.py 中 predefined_cypher 工具描述的 8 大类查询
"""
from typing import Dict

predefined_cypher_dict: Dict[str, str] = {
    # ==================== 1. 菜品属性查询 (recipe_property) ====================
    # 对应 recipe_kg 的 recipe_property 问题类型

    "dish_instructions": """
MATCH (d:Dish {name: $dish_name})
RETURN d.name AS 菜名, d.instructions AS 做法
""",

    "dish_cook_time": """
MATCH (d:Dish {name: $dish_name})
RETURN d.name AS 菜名, d.cook_time AS 耗时
""",

    "dish_flavor": """
MATCH (d:Dish {name: $dish_name})-[:HAS_FLAVOR]->(f:Flavor)
RETURN d.name AS 菜名, collect(f.name) AS 口味
""",

    "dish_cooking_method": """
MATCH (d:Dish {name: $dish_name})-[:USES_METHOD]->(m:CookingMethod)
RETURN d.name AS 菜名, collect(m.name) AS 工艺
""",

    "dish_type": """
MATCH (d:Dish {name: $dish_name})-[:BELONGS_TO_TYPE]->(t:DishType)
RETURN d.name AS 菜名, collect(t.name) AS 类型
""",

    "dish_complete_info": """
MATCH (d:Dish {name: $dish_name})
OPTIONAL MATCH (d)-[:HAS_FLAVOR]->(f:Flavor)
OPTIONAL MATCH (d)-[:USES_METHOD]->(m:CookingMethod)
OPTIONAL MATCH (d)-[:BELONGS_TO_TYPE]->(t:DishType)
RETURN d.name AS 菜名,
       d.cook_time AS 耗时,
       d.instructions AS 做法,
       collect(DISTINCT f.name) AS 口味,
       collect(DISTINCT m.name) AS 工艺,
       collect(DISTINCT t.name) AS 类型
""",

    # ==================== 2. 属性约束查询 (property_constraint) ====================
    # 对应 recipe_kg 的 property_constraint 问题类型

    "dishes_by_flavor": """
MATCH (d:Dish)-[:HAS_FLAVOR]->(f:Flavor {name: $flavor_name})
RETURN d.name AS 菜名 LIMIT 15
""",

    "dishes_by_method": """
MATCH (d:Dish)-[:USES_METHOD]->(m:CookingMethod {name: $method_name})
RETURN d.name AS 菜名 LIMIT 15
""",

    "dishes_by_type": """
MATCH (d:Dish)-[:BELONGS_TO_TYPE]->(t:DishType {name: $type_name})
RETURN d.name AS 菜名 LIMIT 15
""",

    "dishes_by_multi_constraints": """
MATCH (d:Dish)
WHERE
  EXISTS((d)-[:HAS_FLAVOR]->(:Flavor {name: $flavor_name}))
  AND EXISTS((d)-[:USES_METHOD]->(:CookingMethod {name: $method_name}))
RETURN d.name AS 菜名 LIMIT 15
""",

    # ==================== 3. 关系约束查询 (relationship_constraint) ====================
    # 对应 recipe_kg 的 relationship_constraint 问题类型

    "dishes_by_main_ingredient": """
MATCH (d:Dish)-[r:HAS_MAIN_INGREDIENT]->(i:Ingredient {name: $ingredient_name})
RETURN d.name AS 菜名, type(r) AS 关系 LIMIT 15
""",

    "dishes_by_aux_ingredient": """
MATCH (d:Dish)-[r:HAS_AUX_INGREDIENT]->(i:Ingredient {name: $ingredient_name})
RETURN d.name AS 菜名, type(r) AS 关系 LIMIT 15
""",

    "ingredients_of_dish": """
MATCH (d:Dish {name: $dish_name})-[r]->(i:Ingredient)
WHERE type(r) IN ['HAS_MAIN_INGREDIENT', 'HAS_AUX_INGREDIENT']
RETURN i.name AS 食材, type(r) AS 关系类型, r.amount_text AS 用量
""",

    "main_ingredients_of_dish": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_MAIN_INGREDIENT]->(i:Ingredient)
RETURN i.name AS 主食材, r.amount_text AS 用量
""",

    "aux_ingredients_of_dish": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_AUX_INGREDIENT]->(i:Ingredient)
RETURN i.name AS 辅料, r.amount_text AS 用量
""",

    # ==================== 4. 关系用量查询 (relationship_query) ====================
    # 对应 recipe_kg 的 relationship_query 问题类型

    "ingredient_amount_in_dish": """
MATCH (d:Dish {name: $dish_name})-[r]->(i:Ingredient {name: $ingredient_name})
WHERE type(r) IN ['HAS_MAIN_INGREDIENT', 'HAS_AUX_INGREDIENT']
RETURN r.amount_text AS 用量
""",

    "main_ingredient_amount": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_MAIN_INGREDIENT]->(i:Ingredient {name: $ingredient_name})
RETURN r.amount_text AS 用量
""",

    "aux_ingredient_amount": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_AUX_INGREDIENT]->(i:Ingredient {name: $ingredient_name})
RETURN r.amount_text AS 用量
""",

    # ==================== 5. 烹饪步骤查询 ====================

    "cooking_steps": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_STEP]->(s:CookingStep)
RETURN s.order AS 步骤序号, s.instruction AS 步骤说明
ORDER BY s.order
""",

    "step_by_order": """
MATCH (d:Dish {name: $dish_name})-[r:HAS_STEP]->(s:CookingStep {order: $step_order})
RETURN s.order AS 步骤序号, s.instruction AS 步骤说明
""",

    # ==================== 6. 食材营养与功效查询 ====================

    "ingredient_nutrition": """
MATCH (i:Ingredient {name: $ingredient_name})-[:HAS_NUTRITION_PROFILE]->(n:NutritionProfile)
RETURN i.name AS 食材, n.description AS 营养档案
""",

    "ingredient_health_benefits": """
MATCH (i:Ingredient {name: $ingredient_name})-[:HAS_HEALTH_BENEFIT]->(h:HealthBenefit)
RETURN i.name AS 食材, collect(h.name) AS 功效
""",

    "ingredient_complete_info": """
MATCH (i:Ingredient {name: $ingredient_name})
OPTIONAL MATCH (i)-[:HAS_NUTRITION_PROFILE]->(n:NutritionProfile)
OPTIONAL MATCH (i)-[:HAS_HEALTH_BENEFIT]->(h:HealthBenefit)
RETURN i.name AS 食材,
       n.description AS 营养档案,
       collect(DISTINCT h.name) AS 功效
""",

    # ==================== 7. 统计分析查询 ====================

    "most_used_cooking_methods": """
MATCH (d:Dish)-[:USES_METHOD]->(m:CookingMethod)
WITH m.name AS 烹饪方法, count(d) AS 使用次数
RETURN 烹饪方法, 使用次数
ORDER BY 使用次数 DESC LIMIT 10
""",

    "most_popular_flavors": """
MATCH (d:Dish)-[:HAS_FLAVOR]->(f:Flavor)
WITH f.name AS 口味, count(d) AS 菜品数量
RETURN 口味, 菜品数量
ORDER BY 菜品数量 DESC LIMIT 10
""",

    "ingredient_usage_count": """
MATCH (d:Dish)-[r]->(i:Ingredient {name: $ingredient_name})
WHERE type(r) IN ['HAS_MAIN_INGREDIENT', 'HAS_AUX_INGREDIENT']
WITH count(DISTINCT d) AS 菜品数量
RETURN 菜品数量
""",

    "dishes_count_by_type": """
MATCH (d:Dish)-[:BELONGS_TO_TYPE]->(t:DishType)
WITH t.name AS 菜品类型, count(d) AS 菜品数量
RETURN 菜品类型, 菜品数量
ORDER BY 菜品数量 DESC
""",

    # ==================== 8. 综合推荐查询 ====================

    "dishes_with_ingredients": """
MATCH (d:Dish)-[r:HAS_MAIN_INGREDIENT]->(i:Ingredient {name: $ingredient_name})
RETURN d.name AS 菜名, d.instructions AS 做法, d.cook_time AS 耗时
LIMIT 10
""",

    "similar_dishes": """
MATCH (d1:Dish {name: $dish_name})-[:HAS_FLAVOR]->(f:Flavor)<-[:HAS_FLAVOR]-(d2:Dish)
WHERE d1 <> d2
WITH d2, count(f) AS 共同口味数
RETURN d2.name AS 相似菜品, 共同口味数
ORDER BY 共同口味数 DESC LIMIT 10
""",

    "similar_dishes_by_method": """
MATCH (d1:Dish {name: $dish_name})-[:USES_METHOD]->(m:CookingMethod)<-[:USES_METHOD]-(d2:Dish)
WHERE d1 <> d2
RETURN d2.name AS 相似菜品, m.name AS 共同工艺
LIMIT 10
""",
}
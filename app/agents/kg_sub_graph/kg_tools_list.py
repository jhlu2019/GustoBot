"""
菜谱知识图谱工具定义
基于 recipe_kg 模块的问题分类和 Neo4j 菜谱图谱模型
"""
from pydantic import BaseModel
from pydantic import Field


class cypher_query(BaseModel):
    """菜谱知识图谱 Cypher 查询工具

    当用户询问关于菜谱、食材、烹饪方法、口味等信息时，使用此工具生成 Cypher 查询语句。

    适用场景包括：
    - 菜品属性查询（做法、耗时、口味、工艺、类型等）
    - 食材用量查询（某道菜需要多少某种食材）
    - 食材营养和功效查询
    - 烹饪步骤查询
    - 基于属性的菜品筛选（如：所有麻辣口味的菜、所有炒菜等）
    - 基于食材的菜品推荐（如：五花肉可以做什么菜）

    此工具会利用 LLM 生成符合菜谱图谱结构的 Cypher 查询语句。
    """

    task: str = Field(..., description="菜谱相关的查询任务描述，LLM 会根据此任务生成 Cypher 查询语句")


class predefined_cypher(BaseModel):
    """预定义菜谱 Cypher 查询工具

    此工具包含预定义的 Cypher 查询语句，用于快速响应常见的菜谱查询需求。
    基于 recipe_kg 模块的 4 种问题类型和 Neo4j 菜谱图谱模型设计。

    根据用户问题类型，可以选择以下类别的查询：

    1. 菜品属性查询 (recipe_property)：
       - dish_instructions: 查询菜品的详细做法
       - dish_cook_time: 查询菜品的烹饪耗时
       - dish_flavor: 查询菜品的口味标签
       - dish_cooking_method: 查询菜品使用的烹饪工艺
       - dish_type: 查询菜品的类型/菜式分类
       - dish_complete_info: 查询菜品的完整信息（做法、耗时、口味、工艺等）

    2. 属性约束查询 (property_constraint)：
       - dishes_by_flavor: 查询特定口味的所有菜品（如麻辣、咸鲜）
       - dishes_by_method: 查询使用特定烹饪工艺的菜品（如炒、蒸、煮）
       - dishes_by_type: 查询特定类型的菜品（如热菜、凉菜）
       - dishes_by_multi_constraints: 基于多个属性约束的组合查询（如麻辣口味的炒菜）

    3. 关系约束查询 (relationship_constraint)：
       - dishes_by_main_ingredient: 查询使用某主食材的所有菜品
       - dishes_by_aux_ingredient: 查询使用某辅料的所有菜品
       - ingredients_of_dish: 查询某道菜需要的所有食材
       - main_ingredients_of_dish: 查询某道菜的主要食材
       - aux_ingredients_of_dish: 查询某道菜的辅料

    4. 关系用量查询 (relationship_query)：
       - ingredient_amount_in_dish: 查询某道菜中某食材的用量
       - main_ingredient_amount: 查询主食材在某菜品中的用量
       - aux_ingredient_amount: 查询辅料在某菜品中的用量

    5. 烹饪步骤查询：
       - cooking_steps: 查询某道菜的详细烹饪步骤（按顺序）
       - step_by_order: 查询某道菜的特定步骤

    6. 食材营养与功效查询：
       - ingredient_nutrition: 查询食材的营养档案
       - ingredient_health_benefits: 查询食材的食疗功效
       - ingredient_complete_info: 查询食材的完整信息（营养+功效）

    7. 统计分析查询：
       - most_used_cooking_methods: 查询最常用的烹饪方法
       - most_popular_flavors: 查询最常见的口味
       - ingredient_usage_count: 查询某食材在多少道菜中被使用
       - dishes_count_by_type: 统计各类型菜品的数量

    8. 综合推荐查询：
       - dishes_with_ingredients: 查询包含指定食材的菜品及其做法
       - similar_dishes: 查询与某菜品口味或工艺相似的其他菜品

    请根据用户的问题选择最合适的查询，并提供必要的参数（如 $dish_name, $ingredient_name, $flavor_name 等）。
    """

    query: str = Field(..., description="预定义查询的标识符，对应 cypher_dict 中的键")
    parameters: dict = Field(..., description="查询所需的参数字典，如 {'dish_name': '红烧肉', 'ingredient_name': '五花肉'}")


class microsoft_graphrag_query(BaseModel):
    """GraphRAG 知识推理工具

    当用户提出需要深度推理、多跳查询或复杂分析的菜谱问题时，使用此工具。

    适用场景包括：
    - 需要综合多个菜品信息进行分析的问题
    - 复杂的菜谱知识推理（如：根据现有食材推荐多道菜的组合）
    - 跨领域的食疗养生建议（需要结合食材功效和菜品特性）
    - 需要对菜谱知识进行总结、归纳的问题
    - 开放式的烹饪建议和创意菜品设计

    此工具利用 Microsoft GraphRAG 技术进行图谱推理和知识生成。
    """
    query: str = Field(..., description="需要通过 GraphRAG 进行深度推理的复杂菜谱问题")



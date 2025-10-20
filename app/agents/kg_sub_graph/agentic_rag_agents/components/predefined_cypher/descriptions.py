"""预定义菜谱 Cypher 查询的描述信息.

该模块为 recipe_kg 图谱准备的固定查询提供语义描述, 用于帮助 LLM 根据用户提问快速匹配合适的查询。
描述应覆盖查询意图、适用场景以及可能的自然语言问法提示。
"""

# 菜品属性相关查询描述
DISH_PROPERTY_QUERY_DESCRIPTIONS = {
    "dish_instructions": "查询指定菜品的完整做法文本, 适用于用户想了解整道菜的烹饪步骤和细节。",
    "dish_cook_time": "查询某道菜的烹饪耗时信息, 适用于用户询问这道菜需要多久能完成。",
    "dish_flavor": "查询菜品关联的口味标签, 适用于用户想知道一道菜是什麼口味或适合的风味偏好。",
    "dish_cooking_method": "查询菜品所使用的烹饪工艺, 适用于用户关注菜是炒、蒸、炖等哪种做法。",
    "dish_type": "查询菜品所属的菜式/分类, 适用于用户了解这道菜是热菜、凉菜或其他类型。",
    "dish_complete_info": "汇总菜品的耗时、做法、口味、工艺与类型等综合信息, 适用于需要一次性掌握菜谱全貌的场景。",
}

# 条件筛选类查询描述
FILTER_QUERY_DESCRIPTIONS = {
    "dishes_by_flavor": "根据口味标签筛选菜品, 适用于用户想找同一口味的多道菜。",
    "dishes_by_method": "按烹饪工艺筛选菜品, 适用于用户想要类似炒、蒸等特定做法的菜谱。",
    "dishes_by_type": "按菜品类型筛选菜谱, 适用于用户想按热菜、家常菜等分类查找菜。",
    "dishes_by_multi_constraints": "同时按口味和烹饪工艺筛选菜品, 适用于用户提出多条件组合需求时。",
}

# 食材关系类查询描述
INGREDIENT_RELATION_QUERY_DESCRIPTIONS = {
    "dishes_by_main_ingredient": "根据主食材反查菜品, 适用于用户想知道某种食材能做哪些主料菜。",
    "dishes_by_aux_ingredient": "根据辅料/调味料反查菜品, 适用于用户想利用某个辅料安排菜谱。",
    "ingredients_of_dish": "列出菜品所有主辅食材及用量, 适用于用户想完整掌握这道菜需要准备的材料。",
    "main_ingredients_of_dish": "仅查询菜品的主食材和对应用量, 适用于强调菜品主体食材的场景。",
    "aux_ingredients_of_dish": "仅查询菜品的辅料/调味料及用量, 适用于用户关注配料或调味细节。",
}

# 食材用量细查描述
INGREDIENT_AMOUNT_QUERY_DESCRIPTIONS = {
    "ingredient_amount_in_dish": "查询某道菜中指定食材的用量, 无论是主料还是辅料, 适用于确认单一食材份量。",
    "main_ingredient_amount": "查询菜品中某个主食材的用量, 适用于主料精确配比的需求。",
    "aux_ingredient_amount": "查询菜品中某个辅料的用量, 适用于调味料或辅料的定量问题。",
}

# 菜谱步骤相关查询描述
COOKING_STEP_QUERY_DESCRIPTIONS = {
    "cooking_steps": "按顺序列出菜品的全部烹饪步骤, 适用于用户想逐步学习做法。",
    "step_by_order": "查询菜品在特定步骤号对应的烹饪说明, 适用于用户追问某一步的详细说明。",
}

# 食材营养与功效查询描述
INGREDIENT_INFO_QUERY_DESCRIPTIONS = {
    "ingredient_nutrition": "查询食材的营养档案描述, 适用于用户想知道食材的营养价值。",
    "ingredient_health_benefits": "查询食材关联的食疗功效标签, 适用于用户关注食疗或健康益处的问题。",
    "ingredient_complete_info": "综合查询食材的营养说明与功效列表, 适用于需要全方位了解食材的场景。",
}

# 统计分析查询描述
STATS_QUERY_DESCRIPTIONS = {
    "most_used_cooking_methods": "统计最常见的烹饪工艺及使用次数, 适用于用户想了解热门做法趋势。",
    "most_popular_flavors": "统计最常见的口味标签及对应菜品数量, 适用于了解流行口味。",
    "ingredient_usage_count": "统计某个食材在多少道菜中出现, 适用于评估食材用途广度。",
    "dishes_count_by_type": "统计各菜品类型下的菜数量, 适用于查看菜谱类型分布。",
}

# 推荐/相似菜品查询描述
RECOMMENDATION_QUERY_DESCRIPTIONS = {
    "dishes_with_ingredients": "根据指定食材推荐可做的菜品以及基本信息, 适用于“手头有某食材能做什么”类问题。",
    "similar_dishes": "基于口味标签寻找与目标菜相似的其他菜, 适用于想找同风格菜谱的用户。",
    "similar_dishes_by_method": "基于烹饪工艺寻找与目标菜相似的菜, 适用于想尝试相同做法的其他菜品。",
}


# 合并所有查询描述
QUERY_DESCRIPTIONS = {}
QUERY_DESCRIPTIONS.update(DISH_PROPERTY_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(FILTER_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(INGREDIENT_RELATION_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(INGREDIENT_AMOUNT_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(COOKING_STEP_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(INGREDIENT_INFO_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(STATS_QUERY_DESCRIPTIONS)
QUERY_DESCRIPTIONS.update(RECOMMENDATION_QUERY_DESCRIPTIONS)

"""
Domain knowledge for the recipe SQL schema.

These descriptions are derived from the factual documentation under:
- docs/food_table.md
- docs/recipe_kg_schema.md

We surface them to the LLM prompts so that the model has grounded context
about the actual tables, columns, and relationships available in the
recipe management database.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Table level descriptions used to enrich schema prompts.
TABLE_DESCRIPTIONS: Dict[str, str] = {
    "recipes": (
        "菜谱主表，记录菜谱的基础信息、难度、份量、耗时、营养及媒体链接。"
        "主键 id，对应菜系的外键为 cuisine_id。"
    ),
    "recipe_ingredients": (
        "菜谱与食材的关联表，包含用量、加工方式、是否主料及 ingredient_type 分类。"
        "通过 recipe_id 连接菜谱，ingredient_id 连接食材。"
    ),
    "ingredients": (
        "食材基础资料，包含分类、营养成分、存储方式和保质期等属性。"
    ),
    "recipe_steps": (
        "菜谱步骤明细，保存每一步的动作、说明、耗时（duration，单位：分钟）、温度、使用工具等。"
    ),
    "step_tools": (
        "步骤与工具的使用记录，标记特定步骤使用的烹饪工具及用途。"
    ),
    "cooking_tools": (
        "标准化的烹饪工具库，包含类型（锅/刀/烤箱等）、材质和容量信息。"
    ),
    "cuisines": (
        "菜系信息表，存储各菜系名称、烹饪特点及常用工具列表。"
    ),
}

# Column level descriptions used when metadata is missing from Neo4j.
COLUMN_DESCRIPTIONS: Dict[Tuple[str, str], str] = {
    ("recipes", "name"): "菜谱名称。",
    ("recipes", "description"): "菜谱简介或背景说明。",
    ("recipes", "image_url"): "菜谱主图链接。",
    ("recipes", "video_url"): "教学或演示视频链接，可为空。",
    ("recipes", "total_time"): "菜谱总耗时（分钟）。",
    ("recipes", "servings"): "份量（默认 4 人份）。",
    ("recipes", "difficulty"): "制作难度，取值为 easy/medium/hard。",
    ("recipes", "cuisine_id"): "关联菜系 cuisines.id 的外键。",
    ("recipes", "total_calories"): "每份总热量 (kcal)。",
    ("recipes", "total_protein"): "每份蛋白质克数。",
    ("recipes", "total_carbs"): "每份碳水克数。",
    ("recipes", "total_fat"): "每份脂肪克数。",
    ("recipe_ingredients", "recipe_id"): "关联菜谱 recipes.id 的外键。",
    ("recipe_ingredients", "ingredient_id"): "关联食材 ingredients.id 的外键。",
    ("recipe_ingredients", "quantity"): "用量数值或文本（如 200g）。",
    ("recipe_ingredients", "unit"): "用量单位（如 g、ml、勺）。",
    ("recipe_ingredients", "prep_method"): "食材预处理方式（如 切丁、焯水）。",
    ("recipe_ingredients", "prep_time"): "准备耗时（分钟）。",
    ("recipe_ingredients", "is_main"): "是否主料，布尔值。",
    ("recipe_ingredients", "substitute"): "可替换食材说明，若无则为空。",
    ("recipe_ingredients", "adjusted_calories"): "按菜谱用量换算的热量。",
    ("recipe_ingredients", "ingredient_type"): (
        "食材角色分类，取值 main（主料）/auxiliary（辅料）/seasoning（调料）。"
    ),
    ("ingredients", "name"): "食材名称（唯一）。",
    ("ingredients", "category"): "食材类别（如 肉类-原料、蔬菜-辅料）。",
    ("ingredients", "calories"): "每 100g 热量 (kcal)。",
    ("ingredients", "protein"): "每 100g 蛋白质克数。",
    ("ingredients", "carbs"): "每 100g 碳水克数。",
    ("ingredients", "fat"): "每 100g 脂肪克数。",
    ("ingredients", "storage_method"): "推荐存储方式（冷藏、常温等）。",
    ("ingredients", "shelf_life"): "保质期（天）。",
    ("recipe_steps", "recipe_id"): "关联菜谱 recipes.id 的外键。",
    ("recipe_steps", "step_number"): "步骤序号，从 1 开始。",
    ("recipe_steps", "action"): "主要烹饪动作（如 爆炒、炖煮）。",
    ("recipe_steps", "instruction"): "步骤详细说明。",
    ("recipe_steps", "duration"): "本步骤耗时（分钟）。",
    ("recipe_steps", "temperature"): "温度或火候提示（如 大火、中火）。",
    ("recipe_steps", "tools_used"): "JSON 数组，列出使用的工具。",
    ("recipe_steps", "tips"): "步骤提示或注意事项。",
    ("step_tools", "step_id"): "关联步骤 recipe_steps.id 的外键。",
    ("step_tools", "tool_id"): "关联工具 cooking_tools.id 的外键。",
    ("step_tools", "usage"): "工具在该步骤中的用途描述。",
    ("cooking_tools", "name"): "工具名称（唯一）。",
    ("cooking_tools", "type"): "工具类型，枚举 pot/pan/knife/oven/other。",
    ("cooking_tools", "material"): "材质，如 不锈钢、不粘涂层。",
    ("cooking_tools", "capacity"): "容量或规格，如 32cm、5L。",
    ("cuisines", "name"): "菜系名称（唯一）。",
    ("cuisines", "cooking_style"): "烹饪特点文字描述。",
    ("cuisines", "typical_tools"): "JSON 数组，记录常用工具。",
    ("recipes", "total_time"): "整道菜的总耗时（分钟），用于统计或排序。",
    ("cuisines", "code"): "（不存在）cuisines 表没有 code 字段，请使用 name 进行筛选。",
}


RELATIONSHIP_FACTS: List[Dict[str, str]] = [
    {
        "source_table": "recipes",
        "source_column": "cuisine_id",
        "target_table": "cuisines",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "每道菜谱隶属于一个菜系，未指定时可为空。",
    },
    {
        "source_table": "recipe_steps",
        "source_column": "recipe_id",
        "target_table": "recipes",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "菜谱由多条步骤组成，按照 step_number 排序。",
    },
    {
        "source_table": "recipe_ingredients",
        "source_column": "recipe_id",
        "target_table": "recipes",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "菜谱需要的食材列表，与 steps 搭配描述烹饪过程。",
    },
    {
        "source_table": "recipe_ingredients",
        "source_column": "ingredient_id",
        "target_table": "ingredients",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "食材维度信息，包含分类与营养。",
    },
    {
        "source_table": "step_tools",
        "source_column": "step_id",
        "target_table": "recipe_steps",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "步骤使用的具体工具。",
    },
    {
        "source_table": "step_tools",
        "source_column": "tool_id",
        "target_table": "cooking_tools",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "description": "工具基础资料。",
    },
]


DOMAIN_SUMMARY = """
- 数据库为菜谱管理场景，核心实体包含菜谱 (recipes)、食材 (ingredients)、菜谱用料 (recipe_ingredients)、菜谱步骤 (recipe_steps)、步骤使用工具 (step_tools)、烹饪工具 (cooking_tools) 与菜系 (cuisines)。
- recipes.cuisine_id -> cuisines.id；recipe_ingredients.recipe_id / recipe_steps.recipe_id -> recipes.id；
  recipe_ingredients.ingredient_id -> ingredients.id；step_tools.step_id -> recipe_steps.id；step_tools.tool_id -> cooking_tools.id。
- recipes.difficulty 的取值限定为 easy/medium/hard；recipe_ingredients.ingredient_type 的取值限定为 main/auxiliary/seasoning。
- cuisines 表仅包含 id、name、cooking_style、typical_tools 等字段，没有 code 字段；按菜系筛选时请使用 name。
- recipe_steps.duration 字段为整数分钟，汇总步骤耗时时可使用 SUM(recipe_steps.duration) 并自定义别名，如 total_duration_minutes。
- 若需要菜肴总耗时，可使用 recipes.total_time 字段。
- 所有查询均应围绕真实存在的表与字段展开，避免凭空构造表名或字段。
""".strip()

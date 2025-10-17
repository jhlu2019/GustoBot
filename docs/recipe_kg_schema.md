# 菜谱知识图谱设计方案

本方案基于示例菜谱与食材 JSON 数据构建，参考医疗知识图谱的建模方式，为后续扩展到完整菜谱语料提供统一的实体、关系与属性定义。

## 实体类型
| 实体类型 | 中文含义 | 实体数量（当前样例） | 举例 |
| --- | --- | --- | --- |
| Dish | 菜品/菜谱 | 2 | 香肠炒菜干；土豆丝炒烧肉 |
| Ingredient | 食材（含主辅料） | 17 | 香肠；菜干；茼蒿；蚝油 |
| FoodCategory | 食材分类/原料类别 | 6 | 腌制肉类；干菜；叶类蔬菜 |
| Flavor | 口味标签 | 2 | 酱香；咸鲜 |
| CookingMethod | 烹饪工艺 | 1 | 炒 |
| DishType | 菜品类型/菜式 | 1 | 热菜 |
| CookingStep | 烹饪步骤节点 | 18 | “爆香蒜末、豆豉”；“土豆丝炒熟后放入茼蒿段” |
| NutritionProfile | 食材营养档案 | 4 | 艾草营养信息；鹌鹑蛋营养信息 |
| HealthBenefit | 食疗功效条目 | 4 | 艾草驱寒湿；鹌鹑蛋健脑 |

> 注：实体数量统计为当前示例数据中去重后的数量，实际上线时将依据全量菜谱数据动态增长。

## 关系类型
| 关系类型 | 中文含义 | 关系数量（样例） | 举例 |
| --- | --- | --- | --- |
| has_main_ingredient | 菜品-主料 | 4 | <香肠炒菜干, 主料, 香肠> |
| has_auxiliary_ingredient | 菜品-辅料 | 10 | <土豆丝炒烧肉, 辅料, 生抽> |
| belongs_to_type | 菜品-菜品类型 | 2 | <香肠炒菜干, 属于, 热菜> |
| has_flavor | 菜品-口味 | 2 | <香肠炒菜干, 口味, 酱香> |
| uses_cooking_method | 菜品-烹饪工艺 | 2 | <土豆丝炒烧肉, 工艺, 炒> |
| has_cooking_step | 菜品-步骤 | 18 | <香肠炒菜干, 包含步骤, “爆香蒜末、豆豉”> |
| step_uses_ingredient | 步骤-涉及食材 | 22 | <步骤“爆香蒜末、豆豉”, 使用, 豆豉> |
| ingredient_in_category | 食材-所属分类 | 17 | <香肠, 属于, 腌制肉类> |
| enhances_flavor | 食材-强化口味 | 5 | <豆豉, 强化, 酱香> |
| ingredient_health_benefit | 食材-功效 | 8 | <艾草, 具有, 驱寒湿> |
| ingredient_links_nutrition | 食材-营养档案 | 4 | <鹌鹑蛋, 对应, NutritionProfile#鹌鹑蛋> |

> 关系数量基于当前样例推算；`step_uses_ingredient` 可支持后续细粒度的烹饪过程查询与可视化。

## 属性类型
| 属性名称 | 中文含义 | 适用实体 | 举例 |
| --- | --- | --- | --- |
| name | 名称 | 全部实体 | “香肠炒菜干”；“酱香” |
| alias | 别名 | Dish, Ingredient | “腊肠炒菜干”；“腊肠” |
| description | 简述 | Dish, Ingredient, FoodCategory | “传统客家腊味小炒” |
| cook_time | 烹饪耗时 | Dish | “十分钟” |
| taste_note | 风味说明 | Dish, Flavor | “酱香” |
| cooking_method_text | 工艺说明 | Dish | “炒” |
| dish_type_note | 菜品类型说明 | DishType | “热菜” |
| ingredient_role | 食材角色 | Ingredient | “主料”；“辅料” |
| quantity | 用量 | Ingredient（通过关系属性） | “2根”；“200g” |
| nutrition_value | 营养价值文字 | NutritionProfile | “富含维生素A、B族...” |
| health_effect | 食疗功效描述 | HealthBenefit | “理气血，逐寒湿” |
| step_order | 步骤序号 | CookingStep | 1；2；... |
| instruction | 操作说明 | CookingStep | “爆香蒜末、豆豉” |
| tip | 小贴士/注意事项 | Dish, CookingStep | “豆豉勿炒糊” |
| source | 数据来源 | 全部实体 | “示例 JSON；用户录入” |

### 关系属性
- `has_main_ingredient` / `has_auxiliary_ingredient`：`quantity`（用量数值）、`unit`（单位）、`preprocess`（前处理，如“切片”“浸水”）、`is_optional`（布尔，标记可选料）。
- `has_cooking_step`：`step_order`（顺序）、`is_core`（布尔，是否关键步骤）。
- `step_uses_ingredient`：`action`（操作，例如“爆香”“调味”）、`amount_hint`（用量提示文本）。
- `enhances_flavor`：`intensity`（枚举：弱/中/强），用于味型推荐。 

## 建模说明与扩展
- 将营养与功效拆分为 `NutritionProfile` 与 `HealthBenefit`，支持标准化引用与面向健康场景的检索。示例 JSON 中艾草、鹌鹑及其蛋、安康鱼均映射到该设计。
- 通过 `CookingStep` + `step_uses_ingredient` 的细粒度关系，可支持过程问答（Q&A）、可视化流程图及多模态生成等高级功能。
- `FoodCategory` 可扩展为多层级（如“蔬菜 > 叶菜类”），以满足食材分类检索及替换推荐需求。
- 所有实体与关系均保留 `source` 属性，便于追溯数据来源与版本管理。后续接入更多菜谱/食材数据源时，可通过统一 ETL 对应到该模式。

该模式可直接映射到 Neo4j 等图数据库，实现菜谱检索、食材替换、基于营养/功效的智能推荐等应用场景。*** End Patch

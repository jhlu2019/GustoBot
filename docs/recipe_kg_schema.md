# 菜谱知识图谱设计方案

本文档描述当前项目中实际存在的 Neo4j 菜谱图谱模型，仅保留代码已经实现并导入的数据结构，便于后续维护和扩展。

## 实体类型
| Label | 中文含义 | 主要属性 | 备注示例 |
| --- | --- | --- | --- |
| Dish | 菜品/菜谱 | `name`, `cook_time`, `instructions` | 香肠炒菜干；土豆丝炒烧肉 |
| Ingredient | 食材（含主辅料、调味料） | `name` | 香肠；茼蒿；蚝油 |
| Flavor | 口味标签 | `name` | 酱香；咸鲜 |
| CookingMethod | 烹饪工艺 | `name` | 炒 |
| DishType | 菜品类型/菜式 | `name` | 热菜 |
| CookingStep | 烹饪步骤节点 | `name`, `dish_name`, `order`, `instruction` | “香肠炒菜干 - Step 3” |
| NutritionProfile | 食材营养档案 | `name`, `description` | 鹌鹑蛋营养描述 |
| HealthBenefit | 食疗功效条目 | `name` | “理气血，逐寒湿” |

> 所有数值均由 `scripts/recipe_kg_to_csv.py` 自 `data/recipe.json` 与 `data/excipients.json` 中生成，实体标签与属性以 ASCII 命名，属性值保持原始中文。

## 关系类型
| 类型 | 起点 → 终点 | 中文含义 | 主要属性 |
| --- | --- | --- | --- |
| `HAS_MAIN_INGREDIENT` | Dish → Ingredient | 菜品主要食材 | `amount_text`（用量文本） |
| `HAS_AUX_INGREDIENT` | Dish → Ingredient | 菜品辅料/调味料 | `amount_text` |
| `HAS_FLAVOR` | Dish → Flavor | 菜品口味 | — |
| `USES_METHOD` | Dish → CookingMethod | 烹饪工艺 | — |
| `BELONGS_TO_TYPE` | Dish → DishType | 菜品类型 | — |
| `HAS_STEP` | Dish → CookingStep | 包含的烹饪步骤 | `order`（步骤顺序） |
| `HAS_NUTRITION_PROFILE` | Ingredient → NutritionProfile | 食材营养描述 | — |
| `HAS_HEALTH_BENEFIT` | Ingredient → HealthBenefit | 食材功效 | — |

目前图谱不包含其他关系（如步骤与食材、分类层级等），若需要扩展，应同步更新 CSV 生成脚本和导入逻辑。

## 节点与关系属性
- `Dish`：`name`（菜名），`cook_time`（耗时描述），`instructions`（原始做法全文）
- `Ingredient` / `Flavor` / `CookingMethod` / `DishType` / `HealthBenefit`：`name`
- `CookingStep`：`name`，`dish_name`（所属菜品名称），`order`（整数步序），`instruction`（步骤说明）
- `NutritionProfile`：`name`（对应食材名），`description`（营养文字）
- `HAS_MAIN_INGREDIENT` / `HAS_AUX_INGREDIENT`：`amount_text`（原始用量，如“2根”）
- `HAS_STEP`：`order`（与步骤保持一致）

除了上述属性外，无额外字段被写入 Neo4j。

## 数据导入流程
1. `docker compose build neo4j`：利用 `Dockerfile` 中的 `neo4j_seeded` 构建阶段，执行以下动作  
   - 运行 `scripts/recipe_kg_to_csv.py` 将 `data/recipe.json` 与 `data/excipients.json` 转换为 `neo4j-admin` 所需 CSV；  
   - 调用 `neo4j-admin database import` 离线生成 `neo4j` 数据库文件。
2. `docker compose up -d neo4j`：启动后即可直接访问预导入的图谱。
3. 如需重新生成数据，更新 JSON 后重新执行 `docker compose build neo4j`。

此外，应用服务启动时仍保留运行时导入逻辑，可通过环境变量控制是否跳过（`NEO4J_BOOTSTRAP_JSON` 等，详见 `app/config/settings.py`）。

---

该文档与实际代码保持一致，确保使用者在 Neo4j 中看到的实体、关系与属性均与描述准确对应。*** End Patch

# 菜谱管理系统设计 README.md

## 概述
本项目设计一个菜谱管理系统，重点关注**烹饪执行过程**，包括详细的材料清单、步骤、时间控制、工具使用等实际操作信息。淡化作者信息，突出"怎么做"的核心内容。MySQL 用于存储结构化烹饪数据，知识图谱用于分析烹饪模式和相似菜谱推荐。新增食材明细设计，支持将食材分类为原料（主料）、辅料和调料，便于用户快速理解菜谱结构和采购准备。

项目使用 MySQL 8.0+，知识图谱使用 Neo4j。

## MySQL 表设计
以下表设计已更新以支持食材分类：在 `ingredients` 表中扩展 `category` 以支持更细粒度的分类（如"原料"、"辅料"、"调料"），并在 `recipe_ingredients` 表中添加 `ingredient_type` 字段来指定在具体菜谱中的角色（原料、辅料、调料）。这允许全局成分库中定义通用类别，同时在菜谱层面自定义分类。

### 1. 核心表：recipes (菜谱主表)
存储菜谱核心信息和总时长、总营养汇总。

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 菜谱唯一ID                   | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| name           | VARCHAR(255)   | 菜谱名称                     | NOT NULL              | "宫保鸡丁"             |
| description    | TEXT           | 菜谱简介                     |                       | "经典川菜，辣味鸡丁..." |
| image_url      | VARCHAR(500)   | 主图URL                      |                       | "https://example.com/img.jpg" |
| total_time     | INT            | 总用时（分钟）               | DEFAULT 0             | 35                     |
| servings       | INT            | 份量                         | DEFAULT 4             | 4                      |
| difficulty     | ENUM('easy', 'medium', 'hard') | 难度等级             | DEFAULT 'easy'        | 'medium'               |
| cuisine_id     | INT            | 菜系ID（外键）               | FOREIGN KEY (cuisines.id) | 1                      |
| total_calories | DECIMAL(10,2)  | 总热量（kcal，每份）         | DEFAULT 0.00          | 450.50                 |
| total_protein  | DECIMAL(10,2)  | 总蛋白质（g，每份）          | DEFAULT 0.00          | 30.00                  |
| total_carbs    | DECIMAL(10,2)  | 总碳水（g，每份）            | DEFAULT 0.00          | 40.00                  |
| total_fat      | DECIMAL(10,2)  | 总脂肪（g，每份）            | DEFAULT 0.00          | 20.00                  |
| created_at     | TIMESTAMP      | 创建时间                     | DEFAULT CURRENT_TIMESTAMP | 2025-10-14 10:00:00   |
| updated_at     | TIMESTAMP      | 更新时间                     | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 2025-10-14 10:00:00 |

**SQL 创建脚本**：
```sql
CREATE TABLE recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    total_time INT DEFAULT 0,
    servings INT DEFAULT 4,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    cuisine_id INT,
    total_calories DECIMAL(10,2) DEFAULT 0.00,
    total_protein DECIMAL(10,2) DEFAULT 0.00,
    total_carbs DECIMAL(10,2) DEFAULT 0.00,
    total_fat DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cuisine_id) REFERENCES cuisines(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. 材料清单表：recipe_ingredients (菜谱材料)
详细记录每个材料的用量、预处理要求、替换建议。新增加 `ingredient_type` 字段，用于区分原料、辅料、调料。

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 材料ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| recipe_id      | INT            | 菜谱ID（外键）               | FOREIGN KEY (recipes.id) ON DELETE CASCADE | 1                      |
| ingredient_id  | INT            | 成分ID（外键）               | FOREIGN KEY (ingredients.id) | 1                      |
| quantity       | VARCHAR(100)   | 用量                         | NOT NULL              | "200g"                 |
| unit           | VARCHAR(50)    | 单位                         |                       | "g"                    |
| prep_method    | VARCHAR(100)   | 预处理方式                   |                       | "切丁"                 |
| prep_time      | INT            | 预处理时间（分钟）           | DEFAULT 0             | 5                      |
| is_main        | BOOLEAN        | 是否主料                     | DEFAULT FALSE         | TRUE                   |
| substitute     | VARCHAR(255)   | 可替换材料                   |                       | "鸡腿肉"               |
| adjusted_calories | DECIMAL(10,2) | 调整后热量（kcal）           | DEFAULT 0.00          | 330.00                 |
| ingredient_type| ENUM('main', 'auxiliary', 'seasoning') | 食材类型（原料、辅料、调料） | DEFAULT 'auxiliary'   | 'main'                 |

**SQL 创建脚本**：
```sql
CREATE TABLE recipe_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity VARCHAR(100) NOT NULL,
    unit VARCHAR(50),
    prep_method VARCHAR(100),
    prep_time INT DEFAULT 0,
    is_main BOOLEAN DEFAULT FALSE,
    substitute VARCHAR(255),
    adjusted_calories DECIMAL(10,2) DEFAULT 0.00,
    ingredient_type ENUM('main', 'auxiliary', 'seasoning') DEFAULT 'auxiliary',
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT,
    INDEX idx_recipe (recipe_id),
    INDEX idx_main (recipe_id, is_main),
    INDEX idx_type (recipe_id, ingredient_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. 成分库表：ingredients (标准成分库)
存储标准成分的营养和特性信息。扩展 `category` 支持子分类，如"肉类-原料"，以便全局管理食材明细。

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 成分ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| name           | VARCHAR(255)   | 成分名称                     | NOT NULL, UNIQUE      | "鸡胸肉"               |
| category       | VARCHAR(100)   | 分类（如"肉类-原料"、"蔬菜-辅料"、"调味-调料"） |                     | "肉类-原料"            |
| calories       | DECIMAL(10,2)  | 热量（kcal/100g）            | DEFAULT 0.00          | 165.00                 |
| protein        | DECIMAL(10,2)  | 蛋白质（g/100g）             | DEFAULT 0.00          | 31.00                  |
| carbs          | DECIMAL(10,2)  | 碳水（g/100g）               | DEFAULT 0.00          | 0.00                   |
| fat            | DECIMAL(10,2)  | 脂肪（g/100g）               | DEFAULT 0.00          | 3.60                   |
| storage_method | VARCHAR(100)   | 储存方式                     |                       | "冷藏"                 |
| shelf_life     | INT            | 保存期限（天）               | DEFAULT 0             | 3                      |

**SQL 创建脚本**：
```sql
CREATE TABLE ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    calories DECIMAL(10,2) DEFAULT 0.00,
    protein DECIMAL(10,2) DEFAULT 0.00,
    carbs DECIMAL(10,2) DEFAULT 0.00,
    fat DECIMAL(10,2) DEFAULT 0.00,
    storage_method VARCHAR(100),
    shelf_life INT DEFAULT 0,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 4. 烹饪步骤表：recipe_steps (详细步骤)
记录每个烹饪步骤的时间、动作、工具、技巧。（未变更，但可通过查询关联食材明细）

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 步骤ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| recipe_id      | INT            | 菜谱ID（外键）               | FOREIGN KEY (recipes.id) ON DELETE CASCADE | 1                      |
| step_number    | INT            | 步骤序号                     | NOT NULL              | 1                      |
| action         | VARCHAR(100)   | 主要动作                     | NOT NULL              | "爆炒"                 |
| instruction    | TEXT           | 详细说明                     | NOT NULL              | "热油后放入鸡丁..."    |
| duration       | INT            | 本步持续时间（分钟）         | DEFAULT 0             | 3                      |
| temperature    | VARCHAR(50)    | 温度要求                     |                       | "大火"                 |
| tools_used     | JSON           | 使用工具列表                 |                       | ["炒锅", "铲子"]       |
| tips           | TEXT           | 小贴士                       |                       | "火候要掌握好..."      |

**SQL 创建脚本**：
```sql
CREATE TABLE recipe_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    step_number INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    instruction TEXT NOT NULL,
    duration INT DEFAULT 0,
    temperature VARCHAR(50),
    tools_used JSON,
    tips TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_recipe_step (recipe_id, step_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. 工具表：cooking_tools (烹饪工具库)
标准化工具信息，支持步骤中的工具关联。（未变更）

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 工具ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| name           | VARCHAR(100)   | 工具名称                     | NOT NULL, UNIQUE      | "炒锅"                 |
| type           | ENUM('pot', 'pan', 'knife', 'oven', 'other') | 类型 | DEFAULT 'other' | 'pan'                  |
| material       | VARCHAR(50)    | 材质                         |                       | "不粘涂层"             |
| capacity       | VARCHAR(50)    | 容量（如"28cm"）             |                       | "32cm"                 |

**SQL 创建脚本**：
```sql
CREATE TABLE cooking_tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type ENUM('pot', 'pan', 'knife', 'oven', 'other') DEFAULT 'other',
    material VARCHAR(50),
    capacity VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 6. 菜系表：cuisines (菜系信息)
提供菜系的基本烹饪特点。（未变更）

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 菜系ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| name           | VARCHAR(255)   | 菜系名称                     | NOT NULL, UNIQUE      | "川菜"                 |
| cooking_style  | TEXT           | 烹饪特点                     |                       | "重辣重油..."          |
| typical_tools  | JSON           | 常用工具                     |                       | ["砂锅", "炒锅"]       |

**SQL 创建脚本**：
```sql
CREATE TABLE cuisines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    cooking_style TEXT,
    typical_tools JSON
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 7. 步骤-工具关联表：step_tools (步骤工具使用)
记录具体步骤使用的工具和使用方式。（未变更）

| 字段名          | 数据类型       | 描述                          | 约束                  | 示例值                  |
|-----------------|----------------|-------------------------------|-----------------------|-------------------------|
| id             | INT            | 关联ID                       | PRIMARY KEY, AUTO_INCREMENT | 1                      |
| step_id        | INT            | 步骤ID（外键）               | FOREIGN KEY (recipe_steps.id) ON DELETE CASCADE | 1                      |
| tool_id        | INT            | 工具ID（外键）               | FOREIGN KEY (cooking_tools.id) | 1                      |
| usage          | VARCHAR(100)   | 使用方式                     |                       | "主烹饪锅"             |

**SQL 创建脚本**：
```sql
CREATE TABLE step_tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_id INT NOT NULL,
    tool_id INT NOT NULL,
    usage VARCHAR(100),
    FOREIGN KEY (step_id) REFERENCES recipe_steps(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES cooking_tools(id) ON DELETE RESTRICT,
    UNIQUE KEY unique_step_tool (step_id, tool_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 食材明细设计
为突出菜谱的“怎么做”部分，食材明细按以下分类组织：
- **原料（主料）**：菜谱的核心成分，通常决定菜品主体风味和营养（如鸡胸肉、米饭）。在 `recipe_ingredients` 中设置 `ingredient_type = 'main'`，并优先 `is_main = TRUE`。
- **辅料**：辅助增强口感或外观的成分（如花生、青椒）。设置 `ingredient_type = 'auxiliary'`。
- **调料**：用于调味的成分（如酱油、辣椒）。设置 `ingredient_type = 'seasoning'`。

**查询示例**（获取菜谱的食材明细，按分类分组）：
```sql
-- 获取特定菜谱的食材明细，按原料、辅料、调料分类
SELECT 
    ri.ingredient_type AS type,
    i.name AS ingredient_name,
    ri.quantity,
    ri.unit,
    ri.prep_method
FROM recipe_ingredients ri
JOIN ingredients i ON ri.ingredient_id = i.id
WHERE ri.recipe_id = 1
GROUP BY ri.ingredient_type
ORDER BY 
    CASE ri.ingredient_type
        WHEN 'main' THEN 1
        WHEN 'auxiliary' THEN 2
        WHEN 'seasoning' THEN 3
    END;
```

## 知识图谱设计
知识图谱已更新以支持食材明细分类：在 `Ingredient` 实体添加 `ingredient_type` 属性，支持查询如“推荐主料为鸡肉的川菜”。

### 实体类型
- **Recipe**：完整菜谱
- **Ingredient**：具体成分
- **CookingStep**：烹饪步骤
- **CookingAction**：烹饪动作（如"爆炒"、"蒸"）
- **CookingTool**：烹饪工具
- **CuisineStyle**：菜系风格

### 实体属性

**Recipe 属性**：
- name, total_time, difficulty, servings, total_calories
- cooking_method (主烹饪方式，如"炒")

**Ingredient 属性**：
- name, category, prep_method, quantity_needed
- nutritional_profile {calories, protein, carbs, fat}
- ingredient_type (string，如"main"、"auxiliary"、"seasoning")

**CookingStep 属性**：
- step_number, action_type, duration, temperature
- instruction_summary, difficulty_level

**CookingAction 属性**：
- action_name (如"爆炒"), typical_duration, heat_level
- suitable_ingredients (适用食材类型)

**CookingTool 属性**：
- name, type, material, optimal_use (最佳用途)

**CuisineStyle 属性**：
- name, signature_flavors, cooking_temperature
- common_actions (常用烹饪动作)

### 关系类型

**核心烹饪关系**：
- **CONTAINS_STEP**：菜谱包含步骤 (Recipe → CookingStep)
- **USES_INGREDIENT**：步骤使用成分 (CookingStep → Ingredient)
- **PERFORMS_ACTION**：步骤执行动作 (CookingStep → CookingAction)
- **REQUIRES_TOOL**：步骤需要工具 (CookingStep → CookingTool)
- **PREPARES_INGREDIENT**：预处理成分 (CookingStep → Ingredient)

**烹饪模式关系**：
- **FOLLOWED_BY**：步骤顺序 (CookingStep → CookingStep)
- **TYPICAL_FOR**：动作典型用于某种菜系 (CookingAction → CuisineStyle)
- **SUITABLE_FOR**：工具适合某种动作 (CookingTool → CookingAction)

### 关系属性

**CONTAINS_STEP**：
- step_position (步骤位置), estimated_time

**USES_INGREDIENT**：
- quantity_used, prep_state (如"切丁"), ingredient_type (如"main")

**PERFORMS_ACTION**：
- action_intensity (强度), heat_level

**REQUIRES_TOOL**：
- tool_role (主锅/辅具), usage_duration

**Cypher 示例**（包含食材分类）：
```cypher
// 创建烹饪流程并分类食材
CREATE (r:Recipe {name: '宫保鸡丁'})
CREATE (s1:CookingStep {step_number: 1, action: '切配', duration: 10})
CREATE (s2:CookingStep {step_number: 2, action: '爆炒', duration: 5})
CREATE (i_main:Ingredient {name: '鸡胸肉', ingredient_type: 'main'})
CREATE (i_aux:Ingredient {name: '花生', ingredient_type: 'auxiliary'})
CREATE (i_season:Ingredient {name: '辣椒酱', ingredient_type: 'seasoning'})
CREATE (t:CookingTool {name: '炒锅'})

CREATE (r)-[:CONTAINS_STEP {position: 1}]->(s1)
CREATE (s1)-[:USES_INGREDIENT {quantity: '200g', ingredient_type: 'main'}]->(i_main)
CREATE (s1)-[:USES_INGREDIENT {quantity: '50g', ingredient_type: 'auxiliary'}]->(i_aux)
CREATE (s2)-[:USES_INGREDIENT {quantity: '2勺', ingredient_type: 'seasoning'}]->(i_season)
CREATE (r)-[:CONTAINS_STEP {position: 2}]->(s2)
CREATE (s2)-[:REQUIRES_TOOL {role: '主锅'}]->(t)
CREATE (s1)-[:FOLLOWED_BY]->(s2);
```

**查询示例**（查找主料为鸡肉的菜谱）：
```cypher
MATCH (r:Recipe)-[:CONTAINS_STEP]->(s:CookingStep)-[:USES_INGREDIENT {ingredient_type: 'main'}]->(i:Ingredient {name: '鸡胸肉'})
RETURN r.name, collect(s.step_number) as steps;
```

## 实施重点
1. **时间管理**：步骤时间累加验证总时间准确性
2. **工具冲突检测**：同一时间多个步骤不能用同一主工具
3. **材料预处理**：支持批量预处理时间优化，结合食材类型优先处理原料
4. **动作标准化**：建立烹饪动作库，支持智能推荐（如调料适合的动作）
5. **营养计算**：实时计算各步骤营养变化，按食材类型汇总（e.g., 主料贡献的主要热量）
6. **食材明细优化**：应用层可生成分类列表，如“原料：鸡胸肉 200g；辅料：花生 50g；调料：辣椒酱 2勺”

## 查询示例
```sql
-- 获取包含具体步骤的菜谱，并按食材类型汇总
SELECT r.name, rs.action, rs.duration, 
       GROUP_CONCAT(DISTINCT CASE WHEN ri.ingredient_type = 'main' THEN i.name END) AS main_ingredients,
       GROUP_CONCAT(DISTINCT CASE WHEN ri.ingredient_type = 'auxiliary' THEN i.name END) AS auxiliary_ingredients,
       GROUP_CONCAT(DISTINCT CASE WHEN ri.ingredient_type = 'seasoning' THEN i.name END) AS seasonings
FROM recipes r 
JOIN recipe_steps rs ON r.id = rs.recipe_id 
LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
LEFT JOIN ingredients i ON ri.ingredient_id = i.id
WHERE rs.action = '爆炒' AND rs.duration <= 5
GROUP BY r.id, rs.id;
```

---
 
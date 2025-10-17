-- 菜谱管理系统 MySQL 数据库初始化脚本
-- 基于 docs/food_table.md 设计

USE recipe_db;

-- 1. 创建菜系表
CREATE TABLE IF NOT EXISTS cuisines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    cooking_style TEXT,
    typical_tools JSON,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 创建菜谱主表
CREATE TABLE IF NOT EXISTS recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    video_url VARCHAR(500),
    total_time INT DEFAULT 0 COMMENT '总用时(分钟)',
    servings INT DEFAULT 4 COMMENT '份量',
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'easy',
    cuisine_id INT,
    total_calories DECIMAL(10,2) DEFAULT 0.00 COMMENT '总热量(kcal/份)',
    total_protein DECIMAL(10,2) DEFAULT 0.00 COMMENT '总蛋白质(g/份)',
    total_carbs DECIMAL(10,2) DEFAULT 0.00 COMMENT '总碳水(g/份)',
    total_fat DECIMAL(10,2) DEFAULT 0.00 COMMENT '总脂肪(g/份)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cuisine_id) REFERENCES cuisines(id) ON DELETE SET NULL,
    INDEX idx_cuisine (cuisine_id),
    INDEX idx_difficulty (difficulty),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 创建成分库表
CREATE TABLE IF NOT EXISTS ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) COMMENT '分类(如"肉类-原料"、"蔬菜-辅料")',
    calories DECIMAL(10,2) DEFAULT 0.00 COMMENT '热量(kcal/100g)',
    protein DECIMAL(10,2) DEFAULT 0.00 COMMENT '蛋白质(g/100g)',
    carbs DECIMAL(10,2) DEFAULT 0.00 COMMENT '碳水(g/100g)',
    fat DECIMAL(10,2) DEFAULT 0.00 COMMENT '脂肪(g/100g)',
    storage_method VARCHAR(100) COMMENT '储存方式',
    shelf_life INT DEFAULT 0 COMMENT '保存期限(天)',
    INDEX idx_category (category),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 创建菜谱材料关联表
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity VARCHAR(100) NOT NULL COMMENT '用量',
    unit VARCHAR(50) COMMENT '单位',
    prep_method VARCHAR(100) COMMENT '预处理方式',
    prep_time INT DEFAULT 0 COMMENT '预处理时间(分钟)',
    is_main BOOLEAN DEFAULT FALSE COMMENT '是否主料',
    substitute VARCHAR(255) COMMENT '可替换材料',
    adjusted_calories DECIMAL(10,2) DEFAULT 0.00 COMMENT '调整后热量',
    ingredient_type ENUM('main', 'auxiliary', 'seasoning') DEFAULT 'auxiliary' COMMENT '食材类型:原料/辅料/调料',
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT,
    INDEX idx_recipe (recipe_id),
    INDEX idx_ingredient (ingredient_id),
    INDEX idx_main (recipe_id, is_main),
    INDEX idx_type (recipe_id, ingredient_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 创建烹饪工具表
CREATE TABLE IF NOT EXISTS cooking_tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type ENUM('pot', 'pan', 'knife', 'oven', 'other') DEFAULT 'other',
    material VARCHAR(50) COMMENT '材质',
    capacity VARCHAR(50) COMMENT '容量',
    INDEX idx_type (type),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 创建烹饪步骤表
CREATE TABLE IF NOT EXISTS recipe_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipe_id INT NOT NULL,
    step_number INT NOT NULL COMMENT '步骤序号',
    action VARCHAR(100) NOT NULL COMMENT '主要动作',
    instruction TEXT NOT NULL COMMENT '详细说明',
    duration INT DEFAULT 0 COMMENT '本步持续时间(分钟)',
    temperature VARCHAR(50) COMMENT '温度要求',
    tools_used JSON COMMENT '使用工具列表',
    tips TEXT COMMENT '小贴士',
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_recipe_step (recipe_id, step_number),
    INDEX idx_recipe (recipe_id),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 创建步骤-工具关联表
CREATE TABLE IF NOT EXISTS step_tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_id INT NOT NULL,
    tool_id INT NOT NULL,
    usage VARCHAR(100) COMMENT '使用方式',
    FOREIGN KEY (step_id) REFERENCES recipe_steps(id) ON DELETE CASCADE,
    FOREIGN KEY (tool_id) REFERENCES cooking_tools(id) ON DELETE RESTRICT,
    UNIQUE KEY unique_step_tool (step_id, tool_id),
    INDEX idx_step (step_id),
    INDEX idx_tool (tool_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初始化完成
SELECT 'MySQL 数据库初始化完成!' AS message;

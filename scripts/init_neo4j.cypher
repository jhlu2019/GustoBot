// 菜谱管理系统 Neo4j 知识图谱初始化脚本
// 基于 docs/food_table.md 知识图谱设计

// 清空现有数据 (谨慎使用!)
MATCH (n) DETACH DELETE n;

// ========== 1. 创建菜系节点 ==========
CREATE (sichuan:CuisineStyle {
    name: '川菜',
    signature_flavors: '麻辣鲜香',
    cooking_temperature: 'high',
    common_actions: ['爆炒', '干煸', '水煮', '麻辣']
});

CREATE (cantonese:CuisineStyle {
    name: '粤菜',
    signature_flavors: '清淡鲜美',
    cooking_temperature: 'medium',
    common_actions: ['清蒸', '煲汤', '白灼', '炖']
});

CREATE (shandong:CuisineStyle {
    name: '鲁菜',
    signature_flavors: '咸鲜为主',
    cooking_temperature: 'high',
    common_actions: ['爆炒', '红烧', '炸', '烩']
});

// ========== 2. 创建烹饪动作节点 ==========
CREATE (action_stir_fry:CookingAction {
    action_name: '爆炒',
    typical_duration: 5,
    heat_level: 'high',
    suitable_ingredients: ['肉类', '蔬菜']
});

CREATE (action_steam:CookingAction {
    action_name: '清蒸',
    typical_duration: 15,
    heat_level: 'high',
    suitable_ingredients: ['海鲜', '肉类', '蔬菜']
});

CREATE (action_braise:CookingAction {
    action_name: '红烧',
    typical_duration: 60,
    heat_level: 'medium',
    suitable_ingredients: ['肉类', '豆制品']
});

CREATE (action_marinate:CookingAction {
    action_name: '腌制',
    typical_duration: 15,
    heat_level: 'none',
    suitable_ingredients: ['肉类', '海鲜']
});

CREATE (action_prep:CookingAction {
    action_name: '切配',
    typical_duration: 10,
    heat_level: 'none',
    suitable_ingredients: ['所有食材']
});

CREATE (action_season:CookingAction {
    action_name: '调味',
    typical_duration: 2,
    heat_level: 'none',
    suitable_ingredients: ['调料']
});

// ========== 3. 创建烹饪工具节点 ==========
CREATE (tool_wok:CookingTool {
    name: '炒锅',
    type: 'pan',
    material: '不粘涂层',
    optimal_use: '爆炒、煎炸'
});

CREATE (tool_steamer:CookingTool {
    name: '蒸锅',
    type: 'pot',
    material: '不锈钢',
    optimal_use: '蒸制'
});

CREATE (tool_casserole:CookingTool {
    name: '砂锅',
    type: 'pot',
    material: '陶瓷',
    optimal_use: '炖煮、煲汤'
});

CREATE (tool_knife:CookingTool {
    name: '菜刀',
    type: 'knife',
    material: '不锈钢',
    optimal_use: '切配'
});

CREATE (tool_spatula:CookingTool {
    name: '锅铲',
    type: 'other',
    material: '不锈钢',
    optimal_use: '翻炒'
});

// ========== 4. 创建食材节点 ==========
// 原料
CREATE (ing_chicken:Ingredient {
    name: '鸡胸肉',
    category: '肉类-原料',
    ingredient_type: 'main',
    calories: 165.00, protein: 31.00, carbs: 0.00, fat: 3.60
});

CREATE (ing_pork_belly:Ingredient {
    name: '猪五花肉',
    category: '肉类-原料',
    ingredient_type: 'main',
    calories: 518.00, protein: 9.30, carbs: 0.00, fat: 53.00
});

CREATE (ing_fish:Ingredient {
    name: '鲈鱼',
    category: '海鲜-原料',
    ingredient_type: 'main',
    calories: 105.00, protein: 18.60, carbs: 0.00, fat: 3.40
});

// 辅料
CREATE (ing_green_pepper:Ingredient {
    name: '青椒',
    category: '蔬菜-辅料',
    ingredient_type: 'auxiliary',
    calories: 22.00, protein: 1.00, carbs: 4.90, fat: 0.20
});

CREATE (ing_red_pepper:Ingredient {
    name: '红椒',
    category: '蔬菜-辅料',
    ingredient_type: 'auxiliary',
    calories: 20.00, protein: 0.90, carbs: 4.60, fat: 0.20
});

CREATE (ing_scallion:Ingredient {
    name: '大葱',
    category: '蔬菜-辅料',
    ingredient_type: 'auxiliary',
    calories: 30.00, protein: 1.50, carbs: 6.50, fat: 0.30
});

CREATE (ing_ginger:Ingredient {
    name: '生姜',
    category: '蔬菜-辅料',
    ingredient_type: 'auxiliary',
    calories: 41.00, protein: 1.80, carbs: 9.00, fat: 0.70
});

CREATE (ing_garlic:Ingredient {
    name: '大蒜',
    category: '蔬菜-辅料',
    ingredient_type: 'auxiliary',
    calories: 128.00, protein: 4.50, carbs: 27.60, fat: 0.20
});

CREATE (ing_peanut:Ingredient {
    name: '花生',
    category: '坚果-辅料',
    ingredient_type: 'auxiliary',
    calories: 567.00, protein: 24.80, carbs: 21.70, fat: 48.70
});

// 调料
CREATE (ing_soy_sauce:Ingredient {
    name: '酱油',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 63.00, protein: 5.60, carbs: 10.50, fat: 0.00
});

CREATE (ing_cooking_wine:Ingredient {
    name: '料酒',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 60.00, protein: 0.20, carbs: 5.00, fat: 0.00
});

CREATE (ing_sugar:Ingredient {
    name: '白糖',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 400.00, protein: 0.00, carbs: 100.00, fat: 0.00
});

CREATE (ing_oil:Ingredient {
    name: '食用油',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 900.00, protein: 0.00, carbs: 0.00, fat: 100.00
});

CREATE (ing_sichuan_pepper:Ingredient {
    name: '花椒',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 258.00, protein: 6.70, carbs: 51.80, fat: 8.90
});

CREATE (ing_chili_sauce:Ingredient {
    name: '辣椒酱',
    category: '调味-调料',
    ingredient_type: 'seasoning',
    calories: 60.00, protein: 2.00, carbs: 10.00, fat: 1.50
});

// ========== 5. 创建菜谱1: 宫保鸡丁 ==========
CREATE (recipe_gongbao:Recipe {
    name: '宫保鸡丁',
    total_time: 35,
    difficulty: 'medium',
    servings: 4,
    total_calories: 450.50,
    cooking_method: '爆炒',
    video_url: 'https://example.com/gongbao_video.mp4'
});

// 步骤
CREATE (step1_gb:CookingStep {
    step_number: 1,
    action_type: '腌制',
    duration: 15,
    temperature: '常温',
    instruction_summary: '鸡丁腌制入味',
    difficulty_level: 'easy'
});

CREATE (step2_gb:CookingStep {
    step_number: 2,
    action_type: '切配',
    duration: 8,
    temperature: '常温',
    instruction_summary: '准备所有配料',
    difficulty_level: 'easy'
});

CREATE (step3_gb:CookingStep {
    step_number: 3,
    action_type: '调味',
    duration: 2,
    temperature: '常温',
    instruction_summary: '调制酱汁',
    difficulty_level: 'easy'
});

CREATE (step4_gb:CookingStep {
    step_number: 4,
    action_type: '爆炒',
    duration: 5,
    temperature: '大火',
    instruction_summary: '炒鸡丁',
    difficulty_level: 'medium'
});

CREATE (step5_gb:CookingStep {
    step_number: 5,
    action_type: '爆炒',
    duration: 3,
    temperature: '中火',
    instruction_summary: '爆香调料',
    difficulty_level: 'medium'
});

CREATE (step6_gb:CookingStep {
    step_number: 6,
    action_type: '翻炒',
    duration: 2,
    temperature: '大火',
    instruction_summary: '混合翻炒',
    difficulty_level: 'medium'
});

CREATE (step7_gb:CookingStep {
    step_number: 7,
    action_type: '出锅',
    duration: 1,
    temperature: '大火',
    instruction_summary: '加花生出锅',
    difficulty_level: 'easy'
});

// 菜谱-步骤关系
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 1, estimated_time: 15}]->(step1_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 2, estimated_time: 8}]->(step2_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 3, estimated_time: 2}]->(step3_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 4, estimated_time: 5}]->(step4_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 5, estimated_time: 3}]->(step5_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 6, estimated_time: 2}]->(step6_gb);
CREATE (recipe_gongbao)-[:CONTAINS_STEP {position: 7, estimated_time: 1}]->(step7_gb);

// 步骤顺序
CREATE (step1_gb)-[:FOLLOWED_BY]->(step2_gb);
CREATE (step2_gb)-[:FOLLOWED_BY]->(step3_gb);
CREATE (step3_gb)-[:FOLLOWED_BY]->(step4_gb);
CREATE (step4_gb)-[:FOLLOWED_BY]->(step5_gb);
CREATE (step5_gb)-[:FOLLOWED_BY]->(step6_gb);
CREATE (step6_gb)-[:FOLLOWED_BY]->(step7_gb);

// 步骤-食材关系
CREATE (step1_gb)-[:USES_INGREDIENT {quantity_used: '300g', prep_state: '切丁', ingredient_type: 'main'}]->(ing_chicken);
CREATE (step1_gb)-[:USES_INGREDIENT {quantity_used: '10ml', prep_state: '腌制', ingredient_type: 'seasoning'}]->(ing_cooking_wine);

CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '100g', prep_state: '切块', ingredient_type: 'auxiliary'}]->(ing_green_pepper);
CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '50g', prep_state: '切块', ingredient_type: 'auxiliary'}]->(ing_red_pepper);
CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '20g', prep_state: '切段', ingredient_type: 'auxiliary'}]->(ing_scallion);
CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '10g', prep_state: '切片', ingredient_type: 'auxiliary'}]->(ing_ginger);
CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '15g', prep_state: '切末', ingredient_type: 'auxiliary'}]->(ing_garlic);
CREATE (step2_gb)-[:USES_INGREDIENT {quantity_used: '80g', prep_state: '炒香', ingredient_type: 'auxiliary'}]->(ing_peanut);

CREATE (step3_gb)-[:USES_INGREDIENT {quantity_used: '20ml', prep_state: '调汁', ingredient_type: 'seasoning'}]->(ing_soy_sauce);
CREATE (step3_gb)-[:USES_INGREDIENT {quantity_used: '15g', prep_state: '调汁', ingredient_type: 'seasoning'}]->(ing_sugar);

CREATE (step4_gb)-[:USES_INGREDIENT {quantity_used: '30ml', prep_state: '加热', ingredient_type: 'seasoning'}]->(ing_oil);

CREATE (step5_gb)-[:USES_INGREDIENT {quantity_used: '10g', prep_state: '爆香', ingredient_type: 'seasoning'}]->(ing_sichuan_pepper);
CREATE (step5_gb)-[:USES_INGREDIENT {quantity_used: '适量', prep_state: '爆香', ingredient_type: 'seasoning'}]->(ing_chili_sauce);

// 步骤-动作关系
CREATE (step1_gb)-[:PERFORMS_ACTION {action_intensity: 'gentle', heat_level: 'none'}]->(action_marinate);
CREATE (step2_gb)-[:PERFORMS_ACTION {action_intensity: 'medium', heat_level: 'none'}]->(action_prep);
CREATE (step3_gb)-[:PERFORMS_ACTION {action_intensity: 'gentle', heat_level: 'none'}]->(action_season);
CREATE (step4_gb)-[:PERFORMS_ACTION {action_intensity: 'high', heat_level: 'high'}]->(action_stir_fry);
CREATE (step5_gb)-[:PERFORMS_ACTION {action_intensity: 'high', heat_level: 'medium'}]->(action_stir_fry);
CREATE (step6_gb)-[:PERFORMS_ACTION {action_intensity: 'high', heat_level: 'high'}]->(action_stir_fry);

// 步骤-工具关系
CREATE (step2_gb)-[:REQUIRES_TOOL {tool_role: '切配', usage_duration: 8}]->(tool_knife);
CREATE (step4_gb)-[:REQUIRES_TOOL {tool_role: '主锅', usage_duration: 5}]->(tool_wok);
CREATE (step4_gb)-[:REQUIRES_TOOL {tool_role: '翻炒', usage_duration: 5}]->(tool_spatula);
CREATE (step5_gb)-[:REQUIRES_TOOL {tool_role: '主锅', usage_duration: 3}]->(tool_wok);
CREATE (step5_gb)-[:REQUIRES_TOOL {tool_role: '翻炒', usage_duration: 3}]->(tool_spatula);
CREATE (step6_gb)-[:REQUIRES_TOOL {tool_role: '主锅', usage_duration: 2}]->(tool_wok);
CREATE (step6_gb)-[:REQUIRES_TOOL {tool_role: '翻炒', usage_duration: 2}]->(tool_spatula);
CREATE (step7_gb)-[:REQUIRES_TOOL {tool_role: '主锅', usage_duration: 1}]->(tool_wok);

// 菜谱-菜系关系
MATCH (r:Recipe {name: '宫保鸡丁'}), (c:CuisineStyle {name: '川菜'})
CREATE (r)-[:BELONGS_TO]->(c);

// ========== 6. 创建菜谱2: 红烧肉 ==========
CREATE (recipe_hongshao:Recipe {
    name: '红烧肉',
    total_time: 90,
    difficulty: 'medium',
    servings: 4,
    total_calories: 650.00,
    cooking_method: '红烧',
    video_url: 'https://example.com/hongshaorou_video.mp4'
});

CREATE (step1_hs:CookingStep {
    step_number: 1,
    action_type: '焯水',
    duration: 10,
    temperature: '大火',
    instruction_summary: '焯水去腥',
    difficulty_level: 'easy'
});

CREATE (step2_hs:CookingStep {
    step_number: 2,
    action_type: '炒糖色',
    duration: 8,
    temperature: '小火',
    instruction_summary: '炒糖色',
    difficulty_level: 'hard'
});

CREATE (step3_hs:CookingStep {
    step_number: 3,
    action_type: '翻炒',
    duration: 5,
    temperature: '中火',
    instruction_summary: '上色',
    difficulty_level: 'medium'
});

CREATE (step4_hs:CookingStep {
    step_number: 4,
    action_type: '调味',
    duration: 3,
    temperature: '中火',
    instruction_summary: '加调料和水',
    difficulty_level: 'easy'
});

CREATE (step5_hs:CookingStep {
    step_number: 5,
    action_type: '炖煮',
    duration: 60,
    temperature: '小火',
    instruction_summary: '小火慢炖',
    difficulty_level: 'easy'
});

CREATE (step6_hs:CookingStep {
    step_number: 6,
    action_type: '收汁',
    duration: 8,
    temperature: '大火',
    instruction_summary: '大火收汁',
    difficulty_level: 'medium'
});

// 菜谱-步骤关系
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 1, estimated_time: 10}]->(step1_hs);
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 2, estimated_time: 8}]->(step2_hs);
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 3, estimated_time: 5}]->(step3_hs);
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 4, estimated_time: 3}]->(step4_hs);
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 5, estimated_time: 60}]->(step5_hs);
CREATE (recipe_hongshao)-[:CONTAINS_STEP {position: 6, estimated_time: 8}]->(step6_hs);

// 步骤顺序
CREATE (step1_hs)-[:FOLLOWED_BY]->(step2_hs);
CREATE (step2_hs)-[:FOLLOWED_BY]->(step3_hs);
CREATE (step3_hs)-[:FOLLOWED_BY]->(step4_hs);
CREATE (step4_hs)-[:FOLLOWED_BY]->(step5_hs);
CREATE (step5_hs)-[:FOLLOWED_BY]->(step6_hs);

// 步骤-食材关系
CREATE (step1_hs)-[:USES_INGREDIENT {quantity_used: '600g', prep_state: '切块', ingredient_type: 'main'}]->(ing_pork_belly);
CREATE (step1_hs)-[:USES_INGREDIENT {quantity_used: '30ml', prep_state: '焯水', ingredient_type: 'seasoning'}]->(ing_cooking_wine);
CREATE (step1_hs)-[:USES_INGREDIENT {quantity_used: '30g', prep_state: '切片', ingredient_type: 'auxiliary'}]->(ing_ginger);

CREATE (step2_hs)-[:USES_INGREDIENT {quantity_used: '40g', prep_state: '炒制', ingredient_type: 'seasoning'}]->(ing_sugar);
CREATE (step2_hs)-[:USES_INGREDIENT {quantity_used: '30ml', prep_state: '炒制', ingredient_type: 'seasoning'}]->(ing_oil);

CREATE (step4_hs)-[:USES_INGREDIENT {quantity_used: '40ml', prep_state: '调味', ingredient_type: 'seasoning'}]->(ing_soy_sauce);
CREATE (step4_hs)-[:USES_INGREDIENT {quantity_used: '50g', prep_state: '切段', ingredient_type: 'auxiliary'}]->(ing_scallion);

// 步骤-动作关系
CREATE (step2_hs)-[:PERFORMS_ACTION {action_intensity: 'high', heat_level: 'low'}]->(action_stir_fry);
CREATE (step3_hs)-[:PERFORMS_ACTION {action_intensity: 'medium', heat_level: 'medium'}]->(action_stir_fry);
CREATE (step5_hs)-[:PERFORMS_ACTION {action_intensity: 'low', heat_level: 'low'}]->(action_braise);

// 步骤-工具关系
CREATE (step2_hs)-[:REQUIRES_TOOL {tool_role: '炒制', usage_duration: 8}]->(tool_wok);
CREATE (step3_hs)-[:REQUIRES_TOOL {tool_role: '炒制', usage_duration: 5}]->(tool_wok);
CREATE (step3_hs)-[:REQUIRES_TOOL {tool_role: '翻炒', usage_duration: 5}]->(tool_spatula);
CREATE (step5_hs)-[:REQUIRES_TOOL {tool_role: '炖煮', usage_duration: 60}]->(tool_casserole);
CREATE (step6_hs)-[:REQUIRES_TOOL {tool_role: '收汁', usage_duration: 8}]->(tool_casserole);

// 菜谱-菜系关系
MATCH (r:Recipe {name: '红烧肉'}), (c:CuisineStyle {name: '鲁菜'})
CREATE (r)-[:BELONGS_TO]->(c);

// ========== 7. 创建烹饪模式关系 ==========
MATCH (a:CookingAction {action_name: '爆炒'}), (c:CuisineStyle {name: '川菜'})
CREATE (a)-[:TYPICAL_FOR]->(c);

MATCH (a:CookingAction {action_name: '清蒸'}), (c:CuisineStyle {name: '粤菜'})
CREATE (a)-[:TYPICAL_FOR]->(c);

MATCH (a:CookingAction {action_name: '红烧'}), (c:CuisineStyle {name: '鲁菜'})
CREATE (a)-[:TYPICAL_FOR]->(c);

// 工具-动作关系
MATCH (t:CookingTool {name: '炒锅'}), (a:CookingAction {action_name: '爆炒'})
CREATE (t)-[:SUITABLE_FOR]->(a);

MATCH (t:CookingTool {name: '蒸锅'}), (a:CookingAction {action_name: '清蒸'})
CREATE (t)-[:SUITABLE_FOR]->(a);

MATCH (t:CookingTool {name: '砂锅'}), (a:CookingAction {action_name: '红烧'})
CREATE (t)-[:SUITABLE_FOR]->(a);

MATCH (t:CookingTool {name: '菜刀'}), (a:CookingAction {action_name: '切配'})
CREATE (t)-[:SUITABLE_FOR]->(a);

// ========== 8. 创建索引以提高查询性能 ==========
CREATE INDEX recipe_name_idx IF NOT EXISTS FOR (r:Recipe) ON (r.name);
CREATE INDEX ingredient_name_idx IF NOT EXISTS FOR (i:Ingredient) ON (i.name);
CREATE INDEX ingredient_type_idx IF NOT EXISTS FOR (i:Ingredient) ON (i.ingredient_type);
CREATE INDEX cuisine_name_idx IF NOT EXISTS FOR (c:CuisineStyle) ON (c.name);
CREATE INDEX action_name_idx IF NOT EXISTS FOR (a:CookingAction) ON (a.action_name);
CREATE INDEX tool_name_idx IF NOT EXISTS FOR (t:CookingTool) ON (t.name);

// 完成提示
RETURN 'Neo4j 知识图谱初始化完成!' AS message;

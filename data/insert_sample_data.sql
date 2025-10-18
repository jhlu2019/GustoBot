-- Seed data for GustoBot recipe tables.
-- Populates sample cuisines, tools, ingredients, recipes, steps, and relations.

USE recipe_db;
SET NAMES utf8mb4;

START TRANSACTION;

-- Base cuisines
INSERT INTO cuisines (name, cooking_style, typical_tools)
VALUES
    ('川菜', '辣味浓郁，讲究麻辣鲜香与复合口感。', JSON_ARRAY('炒锅', '砂锅')),
    ('粤菜', '清淡鲜美，强调食材本味与火候掌控。', JSON_ARRAY('蒸锅', '炒锅')),
    ('家常菜', '注重方便快捷，口味温和适合日常家庭。', JSON_ARRAY('炒锅', '汤锅')),
    ('湘菜', '香辣酸辣，重油重色，擅用腌制与熏制工艺。', JSON_ARRAY('炒锅', '砂锅'));

-- Cooking tools
INSERT INTO cooking_tools (name, type, material, capacity)
VALUES
    ('炒锅', 'pan', '碳钢', '32cm'),
    ('蒸锅', 'pot', '不锈钢', '28cm'),
    ('汤锅', 'pot', '不锈钢', '5L'),
    ('平底锅', 'pan', '不粘涂层', '28cm'),
    ('电饭煲', 'other', '复合材质', '3L'),
    ('砧板', 'other', '竹', '40cm'),
    ('菜刀', 'knife', '不锈钢', '8寸'),
    ('锅铲', 'other', '不锈钢', '1把'),
    ('腌制碗', 'other', '陶瓷', '2L'),
    ('搅拌碗', 'other', '不锈钢', '2.5L');

-- Ingredient catalog
INSERT INTO ingredients (name, category, calories, protein, carbs, fat, storage_method, shelf_life)
VALUES
    ('鸡胸肉', '肉类-原料', 165.00, 31.00, 0.00, 3.60, '冷藏', 3),
    ('花生米', '坚果-辅料', 567.00, 25.80, 16.10, 49.20, '常温干燥', 30),
    ('青椒', '蔬菜-辅料', 20.00, 0.90, 4.60, 0.20, '冷藏', 5),
    ('干辣椒', '调味-调料', 318.00, 12.00, 56.00, 17.00, '常温干燥', 180),
    ('花椒', '调味-调料', 285.00, 10.00, 30.00, 16.00, '常温干燥', 365),
    ('姜', '香辛-调料', 80.00, 1.80, 17.80, 0.80, '冷藏', 7),
    ('蒜', '香辛-调料', 149.00, 6.40, 33.10, 0.50, '常温通风', 14),
    ('小葱', '蔬菜-辅料', 32.00, 1.80, 7.30, 0.40, '冷藏', 4),
    ('酱油', '调味-调料', 60.00, 8.00, 6.00, 0.10, '常温避光', 365),
    ('白砂糖', '调味-调料', 387.00, 0.00, 100.00, 0.00, '常温干燥', 365),
    ('米醋', '调味-调料', 18.00, 0.10, 0.90, 0.00, '常温避光', 365),
    ('玉米淀粉', '调味-调料', 381.00, 0.00, 91.00, 0.10, '常温干燥', 365),
    ('食用油', '调味-调料', 884.00, 0.00, 0.00, 100.00, '常温避光', 365),
    ('鲈鱼', '水产-原料', 97.00, 18.00, 0.00, 2.60, '冷藏', 2),
    ('料酒', '调味-调料', 52.00, 0.40, 4.60, 0.10, '常温避光', 365),
    ('蒸鱼豉油', '调味-调料', 72.00, 6.00, 10.00, 0.00, '常温避光', 365),
    ('西兰花', '蔬菜-原料', 34.00, 3.70, 6.60, 0.40, '冷藏', 5),
    ('蒜蓉酱', '调味-调料', 120.00, 4.00, 20.00, 2.00, '冷藏', 30),
    ('牛腩', '肉类-原料', 240.00, 18.00, 0.00, 18.00, '冷藏', 2),
    ('番茄', '蔬菜-原料', 18.00, 0.90, 3.90, 0.20, '常温阴凉', 4),
    ('土豆', '蔬菜-辅料', 77.00, 2.00, 17.00, 0.10, '常温通风', 14),
    ('胡萝卜', '蔬菜-辅料', 41.00, 0.90, 10.00, 0.20, '冷藏', 10),
    ('洋葱', '蔬菜-辅料', 40.00, 1.10, 9.30, 0.10, '常温阴凉', 14),
    ('食盐', '调味-调料', 0.00, 0.00, 0.00, 0.00, '常温干燥', 365),
    ('猪肉里脊', '肉类-原料', 143.00, 21.30, 0.00, 5.40, '冷藏', 2),
    ('蚝油', '调味-调料', 72.00, 5.00, 12.00, 1.00, '常温避光', 365),
    ('猪排骨', '肉类-原料', 240.00, 17.00, 0.00, 19.00, '冷藏', 2),
    ('木耳', '菌类-辅料', 25.00, 1.60, 6.20, 0.20, '常温干燥', 180),
    ('郫县豆瓣酱', '调味-调料', 185.00, 6.00, 20.00, 8.00, '常温避光', 365),
    ('嫩豆腐', '豆制品-原料', 70.00, 8.00, 2.00, 3.00, '冷藏', 3),
    ('鸡蛋', '蛋类-原料', 143.00, 12.60, 1.30, 10.60, '冷藏', 10),
    ('虾仁', '水产-原料', 95.00, 21.00, 0.00, 1.00, '冷藏', 2),
    ('黑胡椒碎', '调味-调料', 255.00, 10.00, 64.00, 3.00, '常温干燥', 365),
    ('香菇', '菌类-辅料', 34.00, 2.20, 6.70, 0.30, '冷藏', 5),
    ('小白菜', '蔬菜-原料', 13.00, 1.50, 2.20, 0.20, '冷藏', 3),
    ('粉丝', '粮食-辅料', 332.00, 0.60, 82.00, 0.20, '常温干燥', 180),
    ('香油', '调味-调料', 884.00, 0.00, 0.00, 100.00, '常温避光', 365),
    ('豆豉', '调味-调料', 200.00, 6.00, 30.00, 6.00, '常温避光', 365),
    ('三文鱼', '水产-原料', 208.00, 20.00, 0.00, 13.00, '冷藏', 2),
    ('鸡腿肉', '肉类-原料', 177.00, 17.00, 0.00, 12.00, '冷藏', 2),
    ('牛里脊', '肉类-原料', 191.00, 21.00, 0.00, 12.00, '冷藏', 2),
    ('西葫芦', '蔬菜-原料', 17.00, 1.20, 3.10, 0.30, '冷藏', 4),
    ('玉米粒', '谷物-辅料', 86.00, 3.20, 19.00, 1.20, '冷藏', 4),
    ('青豆', '豆类-辅料', 118.00, 8.00, 21.00, 1.60, '冷藏', 4),
    ('柠檬', '水果-辅料', 29.00, 1.10, 9.30, 0.30, '冷藏', 7);

COMMIT;

-- Cached identifiers for relational inserts
SELECT id INTO @cuisine_sichuan FROM cuisines WHERE name = '川菜';
SELECT id INTO @cuisine_cantonese FROM cuisines WHERE name = '粤菜';
SELECT id INTO @cuisine_home FROM cuisines WHERE name = '家常菜';

SELECT id INTO @tool_wok FROM cooking_tools WHERE name = '炒锅';
SELECT id INTO @tool_steamer FROM cooking_tools WHERE name = '蒸锅';
SELECT id INTO @tool_soup_pot FROM cooking_tools WHERE name = '汤锅';
SELECT id INTO @tool_flat_pan FROM cooking_tools WHERE name = '平底锅';
SELECT id INTO @tool_rice_cooker FROM cooking_tools WHERE name = '电饭煲';
SELECT id INTO @tool_board FROM cooking_tools WHERE name = '砧板';
SELECT id INTO @tool_knife FROM cooking_tools WHERE name = '菜刀';
SELECT id INTO @tool_spatula FROM cooking_tools WHERE name = '锅铲';
SELECT id INTO @tool_marinade_bowl FROM cooking_tools WHERE name = '腌制碗';
SELECT id INTO @tool_mix_bowl FROM cooking_tools WHERE name = '搅拌碗';

SELECT id INTO @ing_chicken FROM ingredients WHERE name = '鸡胸肉';
SELECT id INTO @ing_peanut FROM ingredients WHERE name = '花生米';
SELECT id INTO @ing_green_pepper FROM ingredients WHERE name = '青椒';
SELECT id INTO @ing_dried_chili FROM ingredients WHERE name = '干辣椒';
SELECT id INTO @ing_sichuan_pepper FROM ingredients WHERE name = '花椒';
SELECT id INTO @ing_ginger FROM ingredients WHERE name = '姜';
SELECT id INTO @ing_garlic FROM ingredients WHERE name = '蒜';
SELECT id INTO @ing_scallion FROM ingredients WHERE name = '小葱';
SELECT id INTO @ing_soy_sauce FROM ingredients WHERE name = '酱油';
SELECT id INTO @ing_sugar FROM ingredients WHERE name = '白砂糖';
SELECT id INTO @ing_vinegar FROM ingredients WHERE name = '米醋';
SELECT id INTO @ing_cornstarch FROM ingredients WHERE name = '玉米淀粉';
SELECT id INTO @ing_cooking_oil FROM ingredients WHERE name = '食用油';
SELECT id INTO @ing_sea_bass FROM ingredients WHERE name = '鲈鱼';
SELECT id INTO @ing_shaoxing_wine FROM ingredients WHERE name = '料酒';
SELECT id INTO @ing_steaming_sauce FROM ingredients WHERE name = '蒸鱼豉油';
SELECT id INTO @ing_broccoli FROM ingredients WHERE name = '西兰花';
SELECT id INTO @ing_garlic_paste FROM ingredients WHERE name = '蒜蓉酱';
SELECT id INTO @ing_brisket FROM ingredients WHERE name = '牛腩';
SELECT id INTO @ing_tomato FROM ingredients WHERE name = '番茄';
SELECT id INTO @ing_potato FROM ingredients WHERE name = '土豆';
SELECT id INTO @ing_carrot FROM ingredients WHERE name = '胡萝卜';
SELECT id INTO @ing_onion FROM ingredients WHERE name = '洋葱';
SELECT id INTO @ing_salt FROM ingredients WHERE name = '食盐';
SELECT id INTO @ing_pork_loin FROM ingredients WHERE name = '猪肉里脊';
SELECT id INTO @ing_oyster_sauce FROM ingredients WHERE name = '蚝油';
SELECT id INTO @ing_pork_ribs FROM ingredients WHERE name = '猪排骨';
SELECT id INTO @ing_wood_ear FROM ingredients WHERE name = '木耳';
SELECT id INTO @ing_douban FROM ingredients WHERE name = '郫县豆瓣酱';
SELECT id INTO @ing_soft_tofu FROM ingredients WHERE name = '嫩豆腐';
SELECT id INTO @ing_egg FROM ingredients WHERE name = '鸡蛋';
SELECT id INTO @ing_shrimp FROM ingredients WHERE name = '虾仁';
SELECT id INTO @ing_black_pepper FROM ingredients WHERE name = '黑胡椒碎';
SELECT id INTO @ing_shiitake FROM ingredients WHERE name = '香菇';
SELECT id INTO @ing_bok_choy FROM ingredients WHERE name = '小白菜';
SELECT id INTO @ing_vermicelli FROM ingredients WHERE name = '粉丝';
SELECT id INTO @ing_sesame_oil FROM ingredients WHERE name = '香油';
SELECT id INTO @ing_fermented_black_bean FROM ingredients WHERE name = '豆豉';
SELECT id INTO @ing_salmon FROM ingredients WHERE name = '三文鱼';
SELECT id INTO @ing_chicken_leg FROM ingredients WHERE name = '鸡腿肉';
SELECT id INTO @ing_beef_tenderloin FROM ingredients WHERE name = '牛里脊';
SELECT id INTO @ing_zucchini FROM ingredients WHERE name = '西葫芦';
SELECT id INTO @ing_corn_kernel FROM ingredients WHERE name = '玉米粒';
SELECT id INTO @ing_green_pea FROM ingredients WHERE name = '青豆';
SELECT id INTO @ing_lemon FROM ingredients WHERE name = '柠檬';

START TRANSACTION;

-- Recipe 1: 宫保鸡丁
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '宫保鸡丁',
    '经典川味热菜，鸡丁鲜嫩、花生酥脆，口感麻辣酸甜平衡。',
    'https://images.example.com/gongbao_jiding.jpg',
    'https://videos.example.com/gongbao_jiding.mp4',
    35, 2, 'medium', @cuisine_sichuan,
    520.00, 48.00, 26.00, 28.00
);
SET @recipe_gongbao := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_gongbao, 1, '切配',
    '鸡胸肉切成均匀小丁，加入酱油、料酒、玉米淀粉拌匀腌制10分钟；青椒切丁，蒜姜切末。',
    10, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '鸡丁大小尽量一致，便于受热均匀。'
);
SET @step_gongbao_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_gongbao_1, @tool_board, '切丁'),
    (@step_gongbao_1, @tool_knife, '切丁'),
    (@step_gongbao_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_gongbao, 2, '炸香',
    '锅内放少量油，中小火将花生米炸至微金黄后捞出沥油备用。',
    3, '中小火', JSON_ARRAY('炒锅', '锅铲'),
    '花生米要不停翻动，避免炒糊。'
);
SET @step_gongbao_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_gongbao_2, @tool_wok, '炸制'),
    (@step_gongbao_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_gongbao, 3, '爆炒',
    '锅中留底油，大火爆香干辣椒与花椒，倒入鸡丁翻炒至变色，再加入蒜姜末、调味汁和青椒丁快速翻匀，最后加入花生米起锅。',
    7, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '调味汁提前兑好，倒入后快速翻炒保持脆感。'
);
SET @step_gongbao_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_gongbao_3, @tool_wok, '爆炒'),
    (@step_gongbao_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_gongbao, @ing_chicken, '300', 'g', '切丁腌制', 10, 1, '鸡腿肉', 480.00, 'main'),
    (@recipe_gongbao, @ing_peanut, '60', 'g', '炸香', 3, 0, NULL, 340.00, 'auxiliary'),
    (@recipe_gongbao, @ing_green_pepper, '80', 'g', '切丁', 2, 0, '黄瓜丁', 18.00, 'auxiliary'),
    (@recipe_gongbao, @ing_dried_chili, '8', 'g', '剪段', 1, 0, NULL, 12.00, 'seasoning'),
    (@recipe_gongbao, @ing_sichuan_pepper, '3', 'g', '备用', 0, 0, NULL, 9.00, 'seasoning'),
    (@recipe_gongbao, @ing_ginger, '10', 'g', '切末', 2, 0, NULL, 8.00, 'seasoning'),
    (@recipe_gongbao, @ing_garlic, '15', 'g', '切末', 2, 0, NULL, 22.00, 'seasoning'),
    (@recipe_gongbao, @ing_soy_sauce, '2', '汤匙', '调汁', 1, 0, NULL, 15.00, 'seasoning'),
    (@recipe_gongbao, @ing_vinegar, '1', '汤匙', '调汁', 1, 0, NULL, 5.00, 'seasoning'),
    (@recipe_gongbao, @ing_sugar, '12', 'g', '调汁', 1, 0, NULL, 46.00, 'seasoning'),
    (@recipe_gongbao, @ing_shaoxing_wine, '1', '汤匙', '腌制', 1, 0, NULL, 8.00, 'seasoning'),
    (@recipe_gongbao, @ing_cornstarch, '10', 'g', '腌制', 1, 0, NULL, 38.00, 'seasoning'),
    (@recipe_gongbao, @ing_cooking_oil, '20', 'g', '烹饪', 0, 0, NULL, 176.80, 'seasoning');

-- Recipe 2: 清蒸鲈鱼
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '清蒸鲈鱼',
    '粤式清蒸做法，鱼肉鲜嫩少油，保留海鲜原汁原味。',
    'https://images.example.com/qingzheng_luyu.jpg',
    'https://videos.example.com/qingzheng_luyu.mp4',
    30, 2, 'easy', @cuisine_cantonese,
    360.00, 52.00, 6.00, 12.00
);
SET @recipe_steamed_bass := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_bass, 1, '处理',
    '鲈鱼去鳞去腮，剖腹去内脏，鱼身两侧斜刀划花；姜切片，小葱切段备用。',
    8, '常温', JSON_ARRAY('砧板', '菜刀'),
    '刀花不要太深，约到达鱼骨即可。'
);
SET @step_bass_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_bass_1, @tool_board, '清理'),
    (@step_bass_1, @tool_knife, '改刀');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_bass, 2, '腌制',
    '在鱼身抹上料酒与少许食盐，夹入姜片和葱段，腌制10分钟。',
    10, '常温', JSON_ARRAY('腌制碗'),
    '腌制时给鱼身适度按摩，吸味更均匀。'
);
SET @step_bass_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_bass_2, @tool_marinade_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_bass, 3, '蒸制',
    '蒸锅入水烧开，将鱼置于蒸盘上，大火蒸8分钟后焖2分钟，取出倒掉蒸汁，撒上葱丝热油激香并淋上蒸鱼豉油。',
    12, '大火', JSON_ARRAY('蒸锅', '锅铲'),
    '蒸制时间视鱼大小调整，保持鱼眼凸起即可。'
);
SET @step_bass_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_bass_3, @tool_steamer, '蒸制'),
    (@step_bass_3, @tool_spatula, '淋油');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_steamed_bass, @ing_sea_bass, '1', '条', '清理划刀', 8, 1, NULL, 290.00, 'main'),
    (@recipe_steamed_bass, @ing_ginger, '20', 'g', '切片', 2, 0, NULL, 16.00, 'auxiliary'),
    (@recipe_steamed_bass, @ing_scallion, '15', 'g', '切段', 2, 0, NULL, 5.00, 'auxiliary'),
    (@recipe_steamed_bass, @ing_shaoxing_wine, '15', 'ml', '腌制', 1, 0, NULL, 8.00, 'seasoning'),
    (@recipe_steamed_bass, @ing_salt, '3', 'g', '抹匀', 1, 0, NULL, 0.00, 'seasoning'),
    (@recipe_steamed_bass, @ing_cooking_oil, '12', 'g', '热油激香', 0, 0, NULL, 106.08, 'seasoning'),
    (@recipe_steamed_bass, @ing_steaming_sauce, '20', 'ml', '淋汁', 0, 0, NULL, 14.40, 'seasoning');

-- Recipe 3: 番茄牛腩煲
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '番茄牛腩煲',
    '长时间慢炖的番茄牛腩，汤汁浓郁，蔬菜软糯。',
    'https://images.example.com/fanqie_niunan.jpg',
    'https://videos.example.com/fanqie_niunan.mp4',
    120, 4, 'medium', @cuisine_home,
    1020.00, 92.00, 48.00, 62.00
);
SET @recipe_brisket := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_brisket, 1, '焯水',
    '牛腩冷水下锅，加入姜片和料酒，大火煮沸撇去浮沫后捞出冲洗干净。',
    10, '大火', JSON_ARRAY('汤锅'),
    '焯水后用温水冲净浮沫，汤更清亮。'
);
SET @step_brisket_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_brisket_1, @tool_soup_pot, '焯水');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_brisket, 2, '炖煮',
    '汤锅重新加热少量油炒香洋葱、蒜末，倒入牛腩、番茄块翻炒，加入清水没过食材，放入胡萝卜、料酒，小火慢炖90分钟。',
    95, '小火', JSON_ARRAY('汤锅'),
    '保持微沸状态，以免肉质变柴。'
);
SET @step_brisket_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_brisket_2, @tool_soup_pot, '炖煮');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_brisket, 3, '收汁',
    '加入土豆块和番茄酱汁，调入酱油、白砂糖、食盐，中火收汁15分钟至汤汁浓稠。',
    15, '中火', JSON_ARRAY('汤锅'),
    '收汁至汤汁挂勺即可，避免炒干。'
);
SET @step_brisket_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_brisket_3, @tool_soup_pot, '收汁');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_brisket, @ing_brisket, '600', 'g', '切块焯水', 12, 1, NULL, 960.00, 'main'),
    (@recipe_brisket, @ing_tomato, '400', 'g', '切块', 5, 0, NULL, 72.00, 'auxiliary'),
    (@recipe_brisket, @ing_onion, '120', 'g', '切丝', 3, 0, NULL, 48.00, 'auxiliary'),
    (@recipe_brisket, @ing_carrot, '150', 'g', '切滚刀', 3, 0, NULL, 61.50, 'auxiliary'),
    (@recipe_brisket, @ing_potato, '180', 'g', '切块', 3, 0, NULL, 138.60, 'auxiliary'),
    (@recipe_brisket, @ing_ginger, '10', 'g', '切片', 2, 0, NULL, 8.00, 'seasoning'),
    (@recipe_brisket, @ing_garlic, '12', 'g', '切末', 2, 0, NULL, 17.88, 'seasoning'),
    (@recipe_brisket, @ing_shaoxing_wine, '20', 'ml', '焯水', 1, 0, NULL, 10.40, 'seasoning'),
    (@recipe_brisket, @ing_soy_sauce, '20', 'ml', '调味', 1, 0, NULL, 12.00, 'seasoning'),
    (@recipe_brisket, @ing_sugar, '8', 'g', '调味', 0, 0, NULL, 30.96, 'seasoning'),
    (@recipe_brisket, @ing_salt, '4', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_brisket, @ing_cooking_oil, '18', 'g', '煸香', 0, 0, NULL, 159.12, 'seasoning');

-- Recipe 4: 蒜蓉西兰花
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '蒜蓉西兰花',
    '爽脆西兰花配蒜蓉酱汁，清香提味，健康低脂。',
    'https://images.example.com/suanrong_xilanhua.jpg',
    'https://videos.example.com/suanrong_xilanhua.mp4',
    20, 3, 'easy', @cuisine_home,
    210.00, 18.00, 26.00, 9.00
);
SET @recipe_broccoli := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_broccoli, 1, '焯烫',
    '西兰花掰成小朵洗净，沸水中加入少许食盐和食用油，焯烫2分钟后迅速过冷水沥干。',
    5, '大火', JSON_ARRAY('汤锅'),
    '焯烫时间不宜过长，保持翠绿色与脆度。'
);
SET @step_broccoli_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_broccoli_1, @tool_soup_pot, '焯烫');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_broccoli, 2, '调酱',
    '蒜蓉酱与蚝油、少量清水混合，调成稠度适中的酱汁备用。',
    3, '常温', JSON_ARRAY('搅拌碗'),
    '可加入几滴香油提升香气。'
);
SET @step_broccoli_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_broccoli_2, @tool_mix_bowl, '调酱');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_broccoli, 3, '快炒',
    '热锅倒入少量油爆香蒜末，倒入酱汁和西兰花翻炒均匀，撒少量食盐调味后即可出锅。',
    5, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '保持大火快炒，避免西兰花出水。'
);
SET @step_broccoli_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_broccoli_3, @tool_wok, '翻炒'),
    (@step_broccoli_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_broccoli, @ing_broccoli, '400', 'g', '掰小朵焯烫', 5, 1, NULL, 136.00, 'main'),
    (@recipe_broccoli, @ing_garlic, '15', 'g', '切末', 2, 0, NULL, 22.35, 'seasoning'),
    (@recipe_broccoli, @ing_garlic_paste, '30', 'g', '调酱', 1, 0, NULL, 36.00, 'seasoning'),
    (@recipe_broccoli, @ing_oyster_sauce, '15', 'g', '调酱', 1, 0, NULL, 10.80, 'seasoning'),
    (@recipe_broccoli, @ing_cooking_oil, '12', 'g', '快炒', 0, 0, NULL, 106.08, 'seasoning'),
    (@recipe_broccoli, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 5: 青椒肉丝
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '青椒肉丝',
    '家常川味快手菜，肉丝滑嫩、青椒脆爽下饭。',
    'https://images.example.com/qingjiao_rous.jpg',
    'https://videos.example.com/qingjiao_rous.mp4',
    25, 2, 'easy', @cuisine_sichuan,
    480.00, 36.00, 22.00, 26.00
);
SET @recipe_pork_pepper := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pork_pepper, 1, '切配',
    '猪里脊切细丝加入酱油、料酒、玉米淀粉抓匀腌10分钟；青椒去籽切丝，洋葱切丝，蒜姜切末。',
    8, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '肉丝逆纹切更易保持嫩度。'
);
SET @step_pork_pepper_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pork_pepper_1, @tool_board, '切丝'),
    (@step_pork_pepper_1, @tool_knife, '切丝'),
    (@step_pork_pepper_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pork_pepper, 2, '滑炒',
    '锅中倒油烧至五成热，下肉丝快速滑散炒至变色后盛出。',
    5, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '油温不可过高，滑炒时间控制在1分钟内。'
);
SET @step_pork_pepper_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pork_pepper_2, @tool_wok, '滑炒'),
    (@step_pork_pepper_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pork_pepper, 3, '合炒',
    '锅中留底油爆香蒜姜，加入青椒丝和洋葱丝炒至断生，再倒回肉丝，加入酱油、白砂糖、米醋调味快速翻匀出锅。',
    3, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '保持大火迅速翻炒，避免青椒出水。'
);
SET @step_pork_pepper_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pork_pepper_3, @tool_wok, '翻炒'),
    (@step_pork_pepper_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_pork_pepper, @ing_pork_loin, '280', 'g', '切丝腌制', 10, 1, '鸡胸肉丝', 400.40, 'main'),
    (@recipe_pork_pepper, @ing_green_pepper, '160', 'g', '切丝', 3, 0, NULL, 32.00, 'auxiliary'),
    (@recipe_pork_pepper, @ing_onion, '80', 'g', '切丝', 2, 0, NULL, 32.00, 'auxiliary'),
    (@recipe_pork_pepper, @ing_garlic, '10', 'g', '切末', 1, 0, NULL, 14.90, 'seasoning'),
    (@recipe_pork_pepper, @ing_ginger, '8', 'g', '切末', 1, 0, NULL, 6.40, 'seasoning'),
    (@recipe_pork_pepper, @ing_soy_sauce, '18', 'ml', '调味', 1, 0, NULL, 10.80, 'seasoning'),
    (@recipe_pork_pepper, @ing_sugar, '6', 'g', '调味', 0, 0, NULL, 23.22, 'seasoning'),
    (@recipe_pork_pepper, @ing_vinegar, '5', 'ml', '调味', 0, 0, NULL, 1.80, 'seasoning'),
    (@recipe_pork_pepper, @ing_cornstarch, '12', 'g', '腌制', 1, 0, NULL, 45.72, 'seasoning'),
    (@recipe_pork_pepper, @ing_cooking_oil, '18', 'g', '滑炒', 0, 0, NULL, 159.12, 'seasoning'),
    (@recipe_pork_pepper, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 6: 红烧排骨
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '红烧排骨',
    '家常风味红烧排骨，肉质软糯、酱香浓郁，适合配饭。',
    'https://images.example.com/hongshao_paigu.jpg',
    'https://videos.example.com/hongshao_paigu.mp4',
    60, 3, 'medium', @cuisine_home,
    820.00, 58.00, 24.00, 48.00
);
SET @recipe_braised_ribs := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_braised_ribs, 1, '焯水',
    '排骨冷水下锅，加入姜片和料酒，大火煮沸撇去浮沫后捞出备用。',
    8, '大火', JSON_ARRAY('汤锅'),
    '焯水后用温水冲去血沫，保持汤汁清亮。'
);
SET @step_ribs_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_ribs_1, @tool_soup_pot, '焯水');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_braised_ribs, 2, '煸炒',
    '炒锅中倒入适量油，加入姜片、蒜片爆香，放入排骨煸炒至表面微焦。',
    6, '中大火', JSON_ARRAY('炒锅', '锅铲'),
    '煸炒至排骨微焦可提升焦香味。'
);
SET @step_ribs_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_ribs_2, @tool_wok, '煸炒'),
    (@step_ribs_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_braised_ribs, 3, '红烧',
    '加入酱油、白砂糖、料酒翻匀后倒入热水没过排骨，小火焖煮35分钟，最后大火收汁。',
    35, '小火', JSON_ARRAY('汤锅', '锅铲'),
    '收汁时不断翻动，防止糊底。'
);
SET @step_ribs_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_ribs_3, @tool_soup_pot, '焖煮'),
    (@step_ribs_3, @tool_spatula, '收汁');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_braised_ribs, @ing_pork_ribs, '600', 'g', '切段焯水', 10, 1, NULL, 960.00, 'main'),
    (@recipe_braised_ribs, @ing_ginger, '15', 'g', '切片', 2, 0, NULL, 12.00, 'seasoning'),
    (@recipe_braised_ribs, @ing_garlic, '12', 'g', '拍碎', 1, 0, NULL, 17.88, 'seasoning'),
    (@recipe_braised_ribs, @ing_soy_sauce, '25', 'ml', '调味', 1, 0, NULL, 18.00, 'seasoning'),
    (@recipe_braised_ribs, @ing_sugar, '15', 'g', '调味', 0, 0, NULL, 57.90, 'seasoning'),
    (@recipe_braised_ribs, @ing_shaoxing_wine, '20', 'ml', '焯水', 1, 0, NULL, 10.40, 'seasoning'),
    (@recipe_braised_ribs, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_braised_ribs, @ing_cooking_oil, '20', 'g', '煸炒', 0, 0, NULL, 176.80, 'seasoning');

-- Recipe 7: 鱼香肉丝
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '鱼香肉丝',
    '经典川味鱼香肉丝，酸甜辣平衡，开胃下饭。',
    'https://images.example.com/yuxiang_rousi.jpg',
    'https://videos.example.com/yuxiang_rousi.mp4',
    30, 2, 'medium', @cuisine_sichuan,
    620.00, 40.00, 32.00, 32.00
);
SET @recipe_yuxiang := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_yuxiang, 1, '切配',
    '猪里脊切丝，加酱油、淀粉腌制；胡萝卜、青椒切丝，木耳泡发切丝，蒜姜切末。',
    8, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '木耳提前泡发，切丝长度与肉丝相仿。'
);
SET @step_yuxiang_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_yuxiang_1, @tool_board, '切丝'),
    (@step_yuxiang_1, @tool_knife, '切丝'),
    (@step_yuxiang_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_yuxiang, 2, '兑汁',
    '取小碗加入郫县豆瓣酱、酱油、白砂糖、米醋调成鱼香汁备用。',
    2, '常温', JSON_ARRAY('搅拌碗'),
    '调味汁提前兑好，下锅操作更迅速。'
);
SET @step_yuxiang_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_yuxiang_2, @tool_mix_bowl, '调汁');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_yuxiang, 3, '快炒',
    '热锅多油滑散肉丝至变色盛出，锅内留底油依次下蒜姜末、豆瓣酱炒香，倒入配菜与肉丝，淋入调味汁快速翻炒。',
    5, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '保持大火快炒，防止出水影响口感。'
);
SET @step_yuxiang_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_yuxiang_3, @tool_wok, '翻炒'),
    (@step_yuxiang_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_yuxiang, @ing_pork_loin, '320', 'g', '切丝腌制', 8, 1, NULL, 457.60, 'main'),
    (@recipe_yuxiang, @ing_carrot, '60', 'g', '切丝', 2, 0, NULL, 24.60, 'auxiliary'),
    (@recipe_yuxiang, @ing_green_pepper, '80', 'g', '切丝', 2, 0, NULL, 16.00, 'auxiliary'),
    (@recipe_yuxiang, @ing_wood_ear, '30', 'g', '泡发切丝', 10, 0, NULL, 7.50, 'auxiliary'),
    (@recipe_yuxiang, @ing_douban, '20', 'g', '调汁', 1, 0, NULL, 37.00, 'seasoning'),
    (@recipe_yuxiang, @ing_garlic, '15', 'g', '切末', 2, 0, NULL, 22.35, 'seasoning'),
    (@recipe_yuxiang, @ing_ginger, '10', 'g', '切末', 2, 0, NULL, 8.00, 'seasoning'),
    (@recipe_yuxiang, @ing_sugar, '12', 'g', '调汁', 0, 0, NULL, 46.44, 'seasoning'),
    (@recipe_yuxiang, @ing_vinegar, '15', 'ml', '调汁', 0, 0, NULL, 2.70, 'seasoning'),
    (@recipe_yuxiang, @ing_soy_sauce, '15', 'ml', '调汁', 0, 0, NULL, 10.80, 'seasoning'),
    (@recipe_yuxiang, @ing_cornstarch, '10', 'g', '腌制', 1, 0, NULL, 38.10, 'seasoning'),
    (@recipe_yuxiang, @ing_cooking_oil, '18', 'g', '滑炒', 0, 0, NULL, 159.12, 'seasoning'),
    (@recipe_yuxiang, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 8: 麻婆豆腐
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '麻婆豆腐',
    '麻辣鲜香的川式麻婆豆腐，豆腐嫩滑入味。',
    'https://images.example.com/mapo_tofu.jpg',
    'https://videos.example.com/mapo_tofu.mp4',
    25, 2, 'medium', @cuisine_sichuan,
    480.00, 32.00, 18.00, 30.00
);
SET @recipe_mapo := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mapo, 1, '准备',
    '嫩豆腐切块入盐水焯烫，猪肉剁成末，蒜姜切末，花椒碾碎备用。',
    6, '中火', JSON_ARRAY('砧板', '菜刀', '汤锅'),
    '焯烫可去豆腥且保持豆腐韧性。'
);
SET @step_mapo_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mapo_1, @tool_board, '切块'),
    (@step_mapo_1, @tool_knife, '切块'),
    (@step_mapo_1, @tool_soup_pot, '焯烫');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mapo, 2, '煸炒',
    '热锅下油，下猪肉末煸至出油，加入豆瓣酱、蒜姜末炒出红油。',
    4, '中火', JSON_ARRAY('炒锅', '锅铲'),
    '豆瓣酱炒出红油是关键步骤。'
);
SET @step_mapo_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mapo_2, @tool_wok, '煸炒'),
    (@step_mapo_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mapo, 3, '收汁',
    '加入高汤或热水，放入豆腐煮沸后改小火焖煮5分钟，加入酱油、花椒粉并用水淀粉勾薄芡。',
    8, '小火', JSON_ARRAY('炒锅', '锅铲'),
    '翻动豆腐时动作轻柔避免碎裂。'
);
SET @step_mapo_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mapo_3, @tool_wok, '焖煮'),
    (@step_mapo_3, @tool_spatula, '勾芡');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_mapo, @ing_soft_tofu, '400', 'g', '切块焯烫', 5, 1, NULL, 280.00, 'main'),
    (@recipe_mapo, @ing_pork_loin, '120', 'g', '剁末', 3, 0, NULL, 171.60, 'auxiliary'),
    (@recipe_mapo, @ing_douban, '25', 'g', '炒香', 1, 0, NULL, 46.25, 'seasoning'),
    (@recipe_mapo, @ing_garlic, '15', 'g', '切末', 2, 0, NULL, 22.35, 'seasoning'),
    (@recipe_mapo, @ing_ginger, '10', 'g', '切末', 2, 0, NULL, 8.00, 'seasoning'),
    (@recipe_mapo, @ing_sichuan_pepper, '4', 'g', '碾粉', 1, 0, NULL, 12.00, 'seasoning'),
    (@recipe_mapo, @ing_soy_sauce, '15', 'ml', '调味', 0, 0, NULL, 10.80, 'seasoning'),
    (@recipe_mapo, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_mapo, @ing_cooking_oil, '18', 'g', '煸炒', 0, 0, NULL, 159.12, 'seasoning'),
    (@recipe_mapo, @ing_cornstarch, '8', 'g', '勾芡', 0, 0, NULL, 30.48, 'seasoning');

-- Recipe 9: 番茄炒蛋
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '番茄炒蛋',
    '酸甜柔滑的番茄炒蛋，是经典家常速成菜。',
    'https://images.example.com/fanqie_chao_dan.jpg',
    'https://videos.example.com/fanqie_chao_dan.mp4',
    15, 2, 'easy', @cuisine_home,
    360.00, 22.00, 16.00, 24.00
);
SET @recipe_tomato_egg := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_tomato_egg, 1, '打蛋',
    '鸡蛋打散加入少许盐调味，番茄切块，小葱切段备用。',
    3, '常温', JSON_ARRAY('搅拌碗', '砧板', '菜刀'),
    '蛋液充分打匀更蓬松。'
);
SET @step_tomato_egg_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_tomato_egg_1, @tool_mix_bowl, '打蛋'),
    (@step_tomato_egg_1, @tool_board, '切块'),
    (@step_tomato_egg_1, @tool_knife, '切块');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_tomato_egg, 2, '炒蛋',
    '热锅冷油，倒入蛋液快速翻炒至半凝固，盛出备用。',
    2, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '保持蛋液嫩滑，炒至六成熟即可。'
);
SET @step_tomato_egg_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_tomato_egg_2, @tool_wok, '炒蛋'),
    (@step_tomato_egg_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_tomato_egg, 3, '合炒',
    '锅内留底油，下番茄煸出汁水后加入白砂糖调味，倒回鸡蛋迅速翻炒，撒上小葱即可。',
    3, '中火', JSON_ARRAY('炒锅', '锅铲'),
    '番茄炒出汁再回蛋，味道更融合。'
);
SET @step_tomato_egg_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_tomato_egg_3, @tool_wok, '翻炒'),
    (@step_tomato_egg_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_tomato_egg, @ing_egg, '4', '个', '打散', 2, 1, NULL, 572.00, 'main'),
    (@recipe_tomato_egg, @ing_tomato, '300', 'g', '切块', 2, 0, NULL, 54.00, 'auxiliary'),
    (@recipe_tomato_egg, @ing_scallion, '10', 'g', '切段', 1, 0, NULL, 3.20, 'auxiliary'),
    (@recipe_tomato_egg, @ing_sugar, '6', 'g', '调味', 0, 0, NULL, 23.22, 'seasoning'),
    (@recipe_tomato_egg, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_tomato_egg, @ing_cooking_oil, '16', 'g', '炒制', 0, 0, NULL, 141.44, 'seasoning');

-- Recipe 10: 酸辣土豆丝
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '酸辣土豆丝',
    '脆爽开胃的酸辣土豆丝，酸度与辣度兼备。',
    'https://images.example.com/suanla_tudousi.jpg',
    'https://videos.example.com/suanla_tudousi.mp4',
    18, 2, 'easy', @cuisine_home,
    240.00, 6.00, 40.00, 8.00
);
SET @recipe_suanla_potato := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_suanla_potato, 1, '切丝',
    '土豆切细丝后用冷水浸泡去淀粉，青椒切丝，蒜拍碎备用。',
    6, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '土豆丝浸泡可保持爽脆不粘连。'
);
SET @step_suanla_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_suanla_1, @tool_board, '切丝'),
    (@step_suanla_1, @tool_knife, '切丝'),
    (@step_suanla_1, @tool_mix_bowl, '浸泡');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_suanla_potato, 2, '炝锅',
    '热锅下油，放入干辣椒、花椒和蒜片炝香。',
    1, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '炝锅时间短，避免花椒炒糊。'
);
SET @step_suanla_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_suanla_2, @tool_wok, '炝锅'),
    (@step_suanla_2, @tool_spatula, '翻动');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_suanla_potato, 3, '快炒',
    '倒入沥干的土豆丝和青椒丝大火翻炒2分钟，淋入米醋和盐快速翻匀出锅。',
    3, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '最后淋醋可锁住酸香风味。'
);
SET @step_suanla_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_suanla_3, @tool_wok, '翻炒'),
    (@step_suanla_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_suanla_potato, @ing_potato, '400', 'g', '切丝浸泡', 6, 1, NULL, 308.00, 'main'),
    (@recipe_suanla_potato, @ing_green_pepper, '40', 'g', '切丝', 1, 0, NULL, 8.00, 'auxiliary'),
    (@recipe_suanla_potato, @ing_dried_chili, '6', 'g', '剪段', 1, 0, NULL, 9.00, 'seasoning'),
    (@recipe_suanla_potato, @ing_sichuan_pepper, '3', 'g', '备用', 0, 0, NULL, 9.00, 'seasoning'),
    (@recipe_suanla_potato, @ing_vinegar, '20', 'ml', '淋汁', 0, 0, NULL, 3.60, 'seasoning'),
    (@recipe_suanla_potato, @ing_garlic, '10', 'g', '拍碎', 1, 0, NULL, 14.90, 'seasoning'),
    (@recipe_suanla_potato, @ing_salt, '4', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_suanla_potato, @ing_cooking_oil, '16', 'g', '煸炒', 0, 0, NULL, 141.44, 'seasoning');

-- Recipe 11: 蒜香鸡腿
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '蒜香鸡腿',
    '外酥里嫩的蒜香鸡腿，鲜香多汁。',
    'https://images.example.com/suanxiang_jitui.jpg',
    'https://videos.example.com/suanxiang_jitui.mp4',
    35, 2, 'medium', @cuisine_home,
    540.00, 44.00, 14.00, 34.00
);
SET @recipe_garlic_chicken_thigh := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_garlic_chicken_thigh, 1, '腌制',
    '鸡腿肉去骨切块，加入蒜末、酱油、白砂糖和淀粉抓匀腌制15分钟。',
    15, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '腌制时加入少许淀粉，肉质更嫩滑。'
);
SET @step_garlic_chicken_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_garlic_chicken_1, @tool_board, '去骨'),
    (@step_garlic_chicken_1, @tool_knife, '切块'),
    (@step_garlic_chicken_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_garlic_chicken_thigh, 2, '煎制',
    '平底锅中倒油烧热，将鸡腿肉皮朝下煎至金黄后翻面煎熟。',
    8, '中火', JSON_ARRAY('平底锅', '锅铲'),
    '先煎带皮面，可逼出鸡油使外皮更酥。'
);
SET @step_garlic_chicken_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_garlic_chicken_2, @tool_flat_pan, '煎制'),
    (@step_garlic_chicken_2, @tool_spatula, '翻面');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_garlic_chicken_thigh, 3, '收汁',
    '加入少量清水，撒入蒜末快速翻匀收汁，装盘即可。',
    2, '大火', JSON_ARRAY('平底锅', '锅铲'),
    '收汁时保持大火，汁浓味更足。'
);
SET @step_garlic_chicken_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_garlic_chicken_3, @tool_flat_pan, '收汁'),
    (@step_garlic_chicken_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_garlic_chicken_thigh, @ing_chicken_leg, '400', 'g', '去骨切块', 10, 1, NULL, 708.00, 'main'),
    (@recipe_garlic_chicken_thigh, @ing_garlic, '20', 'g', '切末', 3, 0, NULL, 29.80, 'seasoning'),
    (@recipe_garlic_chicken_thigh, @ing_soy_sauce, '20', 'ml', '腌制', 1, 0, NULL, 14.40, 'seasoning'),
    (@recipe_garlic_chicken_thigh, @ing_sugar, '10', 'g', '腌制', 0, 0, NULL, 38.70, 'seasoning'),
    (@recipe_garlic_chicken_thigh, @ing_cornstarch, '10', 'g', '腌制', 1, 0, NULL, 38.10, 'seasoning'),
    (@recipe_garlic_chicken_thigh, @ing_cooking_oil, '18', 'g', '煎制', 0, 0, NULL, 159.12, 'seasoning'),
    (@recipe_garlic_chicken_thigh, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 12: 黑椒牛柳
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '黑椒牛柳',
    '黑胡椒香气浓郁的快炒牛柳，肉质鲜嫩。',
    'https://images.example.com/heijiao_niuliu.jpg',
    'https://videos.example.com/heijiao_niuliu.mp4',
    25, 2, 'medium', @cuisine_home,
    510.00, 42.00, 20.00, 26.00
);
SET @recipe_blackpepper_beef := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackpepper_beef, 1, '切配',
    '牛里脊切条，加入黑胡椒、酱油、淀粉腌制；洋葱、青椒切条备用。',
    6, '常温', JSON_ARRAY('砧板', '菜刀', '搅拌碗'),
    '牛柳逆纹切条，口感更嫩。'
);
SET @step_blackpepper_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackpepper_1, @tool_board, '切条'),
    (@step_blackpepper_1, @tool_knife, '切条'),
    (@step_blackpepper_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackpepper_beef, 2, '滑炒',
    '热锅下油，将牛柳快速滑散至变色即盛出。',
    2, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '滑炒时间短，保持牛柳嫩度。'
);
SET @step_blackpepper_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackpepper_2, @tool_wok, '滑炒'),
    (@step_blackpepper_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackpepper_beef, 3, '合炒',
    '锅内留底油，下洋葱与青椒炒香，倒入牛柳、黑胡椒碎和调味料快速翻匀出锅。',
    3, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '最后可加少许清水勾薄芡锁住汁水。'
);
SET @step_blackpepper_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackpepper_3, @tool_wok, '翻炒'),
    (@step_blackpepper_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_blackpepper_beef, @ing_beef_tenderloin, '300', 'g', '切条腌制', 6, 1, NULL, 573.00, 'main'),
    (@recipe_blackpepper_beef, @ing_onion, '80', 'g', '切条', 2, 0, NULL, 32.00, 'auxiliary'),
    (@recipe_blackpepper_beef, @ing_green_pepper, '60', 'g', '切条', 2, 0, NULL, 12.00, 'auxiliary'),
    (@recipe_blackpepper_beef, @ing_black_pepper, '6', 'g', '压碎', 1, 0, NULL, 15.30, 'seasoning'),
    (@recipe_blackpepper_beef, @ing_soy_sauce, '18', 'ml', '调味', 0, 0, NULL, 12.96, 'seasoning'),
    (@recipe_blackpepper_beef, @ing_sugar, '6', 'g', '调味', 0, 0, NULL, 23.22, 'seasoning'),
    (@recipe_blackpepper_beef, @ing_cornstarch, '10', 'g', '腌制', 1, 0, NULL, 38.10, 'seasoning'),
    (@recipe_blackpepper_beef, @ing_cooking_oil, '16', 'g', '滑炒', 0, 0, NULL, 141.44, 'seasoning'),
    (@recipe_blackpepper_beef, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 13: 香菇小白菜
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '香菇小白菜',
    '爽口小白菜配香菇鲜味，清淡不寡淡。',
    'https://images.example.com/xianggu_xiaobaicai.jpg',
    'https://videos.example.com/xianggu_xiaobaicai.mp4',
    15, 2, 'easy', @cuisine_home,
    160.00, 10.00, 14.00, 6.00
);
SET @recipe_mushroom_greens := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mushroom_greens, 1, '焯烫',
    '小白菜洗净切段，香菇去根切片，入沸水焯烫30秒后迅速过凉水。',
    2, '大火', JSON_ARRAY('汤锅'),
    '焯烫时间短，可保持脆嫩口感。'
);
SET @step_mushroom_greens_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mushroom_greens_1, @tool_soup_pot, '焯烫');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mushroom_greens, 2, '快炒',
    '热锅倒油，下蒜末爆香，倒入香菇与小白菜快速翻炒，加入蚝油调味。',
    3, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '快速翻炒让菜叶保持亮泽。'
);
SET @step_mushroom_greens_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mushroom_greens_2, @tool_wok, '翻炒'),
    (@step_mushroom_greens_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_mushroom_greens, 3, '调味',
    '加入盐，淋入香油翻匀即可出锅。',
    1, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '香油最后加入能锁住香气。'
);
SET @step_mushroom_greens_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_mushroom_greens_3, @tool_wok, '翻炒'),
    (@step_mushroom_greens_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_mushroom_greens, @ing_bok_choy, '250', 'g', '切段焯烫', 3, 1, NULL, 32.50, 'main'),
    (@recipe_mushroom_greens, @ing_shiitake, '100', 'g', '切片', 2, 0, NULL, 34.00, 'auxiliary'),
    (@recipe_mushroom_greens, @ing_garlic, '10', 'g', '切末', 1, 0, NULL, 14.90, 'seasoning'),
    (@recipe_mushroom_greens, @ing_oyster_sauce, '12', 'g', '调味', 0, 0, NULL, 8.64, 'seasoning'),
    (@recipe_mushroom_greens, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_mushroom_greens, @ing_cooking_oil, '12', 'g', '翻炒', 0, 0, NULL, 106.08, 'seasoning'),
    (@recipe_mushroom_greens, @ing_sesame_oil, '6', 'ml', '提香', 0, 0, NULL, 53.04, 'seasoning');

-- Recipe 14: 虾仁玉米粒
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '虾仁玉米粒',
    '色彩鲜艳的虾仁玉米粒，营养均衡。',
    'https://images.example.com/xiaoren_yumili.jpg',
    'https://videos.example.com/xiaoren_yumili.mp4',
    18, 2, 'easy', @cuisine_home,
    320.00, 28.00, 26.00, 12.00
);
SET @recipe_shrimp_corn := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_shrimp_corn, 1, '准备',
    '虾仁去虾线，用少许盐和淀粉抓匀；玉米粒、青豆、胡萝卜丁焯水备用。',
    4, '中火', JSON_ARRAY('砧板', '菜刀', '汤锅'),
    '焯水可以保持食材色泽鲜亮。'
);
SET @step_shrimp_corn_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_corn_1, @tool_board, '处理'),
    (@step_shrimp_corn_1, @tool_knife, '切丁'),
    (@step_shrimp_corn_1, @tool_soup_pot, '焯水');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_shrimp_corn, 2, '滑炒',
    '热锅下油，放入虾仁快速滑炒至变色盛出。',
    1, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '虾仁刚变色就要盛出，避免过熟。'
);
SET @step_shrimp_corn_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_corn_2, @tool_wok, '滑炒'),
    (@step_shrimp_corn_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_shrimp_corn, 3, '合炒',
    '锅内留底油，下玉米粒、青豆与胡萝卜丁翻炒1分钟，加入虾仁和调味料翻匀即可出锅。',
    2, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '可加入少许清水勾薄芡让口感更润。'
);
SET @step_shrimp_corn_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_corn_3, @tool_wok, '翻炒'),
    (@step_shrimp_corn_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_shrimp_corn, @ing_shrimp, '200', 'g', '去虾线腌制', 4, 1, NULL, 190.00, 'main'),
    (@recipe_shrimp_corn, @ing_corn_kernel, '120', 'g', '焯水', 2, 0, NULL, 103.20, 'auxiliary'),
    (@recipe_shrimp_corn, @ing_green_pea, '80', 'g', '焯水', 2, 0, NULL, 94.40, 'auxiliary'),
    (@recipe_shrimp_corn, @ing_carrot, '60', 'g', '切丁焯水', 2, 0, NULL, 24.60, 'auxiliary'),
    (@recipe_shrimp_corn, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_shrimp_corn, @ing_sugar, '4', 'g', '调味', 0, 0, NULL, 15.48, 'seasoning'),
    (@recipe_shrimp_corn, @ing_cooking_oil, '14', 'g', '滑炒', 0, 0, NULL, 123.76, 'seasoning'),
    (@recipe_shrimp_corn, @ing_cornstarch, '6', 'g', '腌制', 1, 0, NULL, 22.86, 'seasoning');

-- Recipe 15: 蒜蓉粉丝蒸虾
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '蒜蓉粉丝蒸虾',
    '蒜香浓郁的粉丝蒸虾，鲜美清爽。',
    'https://images.example.com/suanrong_fensi_zhengxia.jpg',
    'https://videos.example.com/suanrong_fensi_zhengxia.mp4',
    22, 2, 'easy', @cuisine_cantonese,
    280.00, 28.00, 24.00, 10.00
);
SET @recipe_steamed_shrimp_vermicelli := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_shrimp_vermicelli, 1, '泡粉丝',
    '粉丝用温水泡软沥干，虾仁去虾线备用。',
    6, '常温', JSON_ARRAY('搅拌碗'),
    '粉丝不要泡太久，保持弹性。'
);
SET @step_shrimp_vermicelli_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_vermicelli_1, @tool_mix_bowl, '泡发');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_shrimp_vermicelli, 2, '调蒜蓉',
    '蒜末与酱油、香油拌匀铺在粉丝上，再摆入虾仁。',
    3, '常温', JSON_ARRAY('搅拌碗'),
    '蒜蓉铺匀能让虾仁均匀入味。'
);
SET @step_shrimp_vermicelli_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_vermicelli_2, @tool_mix_bowl, '调味');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_steamed_shrimp_vermicelli, 3, '蒸制',
    '蒸锅水开后入锅，大火蒸8分钟，取出撒盐即可。',
    8, '大火', JSON_ARRAY('蒸锅'),
    '蒸制时间依虾大小微调，保持鲜嫩。'
);
SET @step_shrimp_vermicelli_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_shrimp_vermicelli_3, @tool_steamer, '蒸制');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_steamed_shrimp_vermicelli, @ing_shrimp, '220', 'g', '去虾线', 4, 1, NULL, 209.00, 'main'),
    (@recipe_steamed_shrimp_vermicelli, @ing_vermicelli, '80', 'g', '泡软', 6, 0, NULL, 265.60, 'auxiliary'),
    (@recipe_steamed_shrimp_vermicelli, @ing_garlic, '25', 'g', '切末', 2, 0, NULL, 37.25, 'seasoning'),
    (@recipe_steamed_shrimp_vermicelli, @ing_soy_sauce, '15', 'ml', '调味', 0, 0, NULL, 10.80, 'seasoning'),
    (@recipe_steamed_shrimp_vermicelli, @ing_sesame_oil, '8', 'ml', '调味', 0, 0, NULL, 70.72, 'seasoning'),
    (@recipe_steamed_shrimp_vermicelli, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 16: 清炒西葫芦
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '清炒西葫芦',
    '口感清爽的清炒西葫芦，低脂轻负担。',
    'https://images.example.com/qingchao_xihulu.jpg',
    'https://videos.example.com/qingchao_xihulu.mp4',
    12, 2, 'easy', @cuisine_home,
    180.00, 6.00, 16.00, 10.00
);
SET @recipe_sauteed_zucchini := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_sauteed_zucchini, 1, '切配',
    '西葫芦切薄片，胡萝卜切丝，蒜切片备用。',
    3, '常温', JSON_ARRAY('砧板', '菜刀'),
    '切片厚度一致，受热更均匀。'
);
SET @step_zucchini_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_zucchini_1, @tool_board, '切片'),
    (@step_zucchini_1, @tool_knife, '切配');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_sauteed_zucchini, 2, '爆香',
    '热锅下油，放入蒜片与胡萝卜丝炒香。',
    1, '中火', JSON_ARRAY('炒锅', '锅铲'),
    '蒜片出香味即可，不可炒糊。'
);
SET @step_zucchini_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_zucchini_2, @tool_wok, '爆香'),
    (@step_zucchini_2, @tool_spatula, '翻炒');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_sauteed_zucchini, 3, '快炒',
    '倒入西葫芦片大火快炒2分钟，加入盐和白砂糖调味即可出锅。',
    2, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '火力要大，保持西葫芦爽脆。'
);
SET @step_zucchini_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_zucchini_3, @tool_wok, '翻炒'),
    (@step_zucchini_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_sauteed_zucchini, @ing_zucchini, '300', 'g', '切片', 3, 1, NULL, 51.00, 'main'),
    (@recipe_sauteed_zucchini, @ing_carrot, '40', 'g', '切丝', 1, 0, NULL, 16.40, 'auxiliary'),
    (@recipe_sauteed_zucchini, @ing_garlic, '8', 'g', '切片', 1, 0, NULL, 11.92, 'seasoning'),
    (@recipe_sauteed_zucchini, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_sauteed_zucchini, @ing_sugar, '4', 'g', '调味', 0, 0, NULL, 15.48, 'seasoning'),
    (@recipe_sauteed_zucchini, @ing_cooking_oil, '14', 'g', '快炒', 0, 0, NULL, 123.76, 'seasoning');

-- Recipe 17: 柠檬蒸三文鱼
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '柠檬蒸三文鱼',
    '清爽低脂的柠檬蒸三文鱼，锁住鱼肉鲜嫩。',
    'https://images.example.com/ningmeng_zheng_sanwenyu.jpg',
    'https://videos.example.com/ningmeng_zheng_sanwenyu.mp4',
    25, 2, 'easy', @cuisine_cantonese,
    420.00, 38.00, 8.00, 26.00
);
SET @recipe_lemon_salmon := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_lemon_salmon, 1, '腌制',
    '三文鱼切块放入腌制碗，加入姜片、柠檬片、盐和香油轻轻抹匀腌制10分钟。',
    10, '常温', JSON_ARRAY('砧板', '菜刀', '腌制碗'),
    '柠檬片轻压出汁，腌制更入味。'
);
SET @step_lemon_salmon_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_lemon_salmon_1, @tool_board, '切块'),
    (@step_lemon_salmon_1, @tool_knife, '切块'),
    (@step_lemon_salmon_1, @tool_marinade_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_lemon_salmon, 2, '蒸制',
    '蒸锅水开后放入三文鱼，大火蒸8分钟。',
    8, '大火', JSON_ARRAY('蒸锅'),
    '蒸制时间依据鱼块厚度调整，保持嫩度。'
);
SET @step_lemon_salmon_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_lemon_salmon_2, @tool_steamer, '蒸制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_lemon_salmon, 3, '调味',
    '取出后淋少许香油，挤入柠檬汁即可享用。',
    1, '常温', JSON_ARRAY('腌制碗'),
    '蒸后调味更能保留柠檬清香。'
);
SET @step_lemon_salmon_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_lemon_salmon_3, @tool_marinade_bowl, '调味');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_lemon_salmon, @ing_salmon, '280', 'g', '切块腌制', 10, 1, NULL, 582.40, 'main'),
    (@recipe_lemon_salmon, @ing_lemon, '1', '个', '切片挤汁', 2, 0, NULL, 29.00, 'auxiliary'),
    (@recipe_lemon_salmon, @ing_ginger, '10', 'g', '切片', 1, 0, NULL, 8.00, 'seasoning'),
    (@recipe_lemon_salmon, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_lemon_salmon, @ing_sesame_oil, '6', 'ml', '调味', 0, 0, NULL, 53.04, 'seasoning'),
    (@recipe_lemon_salmon, @ing_cooking_oil, '12', 'g', '抹油', 0, 0, NULL, 106.08, 'seasoning');

-- Recipe 18: 豆豉蒸排骨
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '豆豉蒸排骨',
    '经典广式豆豉蒸排骨，鲜香入味带回甘。',
    'https://images.example.com/douchi_zheng_paigu.jpg',
    'https://videos.example.com/douchi_zheng_paigu.mp4',
    35, 2, 'medium', @cuisine_cantonese,
    620.00, 42.00, 18.00, 38.00
);
SET @recipe_blackbean_ribs := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackbean_ribs, 1, '腌制',
    '排骨切小段，加入豆豉、蒜末、酱油、白砂糖、蚝油抓匀腌制15分钟。',
    15, '常温', JSON_ARRAY('砧板', '菜刀', '腌制碗'),
    '腌制时可加入少许淀粉锁汁。'
);
SET @step_blackbean_ribs_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackbean_ribs_1, @tool_board, '切段'),
    (@step_blackbean_ribs_1, @tool_knife, '切段'),
    (@step_blackbean_ribs_1, @tool_marinade_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackbean_ribs, 2, '蒸制',
    '蒸锅水开后，将排骨连同腌汁一起放入蒸盘，大火蒸18分钟。',
    18, '大火', JSON_ARRAY('蒸锅'),
    '蒸至排骨轻易脱骨即可。'
);
SET @step_blackbean_ribs_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackbean_ribs_2, @tool_steamer, '蒸制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_blackbean_ribs, 3, '调味',
    '出锅后撒上葱花或少许香油提香即可食用。',
    1, '常温', JSON_ARRAY('腌制碗'),
    '可适量调入盐调节咸度。'
);
SET @step_blackbean_ribs_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_blackbean_ribs_3, @tool_marinade_bowl, '调味');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_blackbean_ribs, @ing_pork_ribs, '450', 'g', '切段腌制', 10, 1, NULL, 720.00, 'main'),
    (@recipe_blackbean_ribs, @ing_fermented_black_bean, '20', 'g', '剁碎', 1, 0, NULL, 40.00, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_garlic, '15', 'g', '切末', 2, 0, NULL, 22.35, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_soy_sauce, '15', 'ml', '腌制', 0, 0, NULL, 10.80, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_sugar, '8', 'g', '腌制', 0, 0, NULL, 30.96, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_oyster_sauce, '10', 'g', '腌制', 0, 0, NULL, 7.20, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_cooking_oil, '10', 'g', '腌制', 0, 0, NULL, 88.40, 'seasoning'),
    (@recipe_blackbean_ribs, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

-- Recipe 19: 家常豆腐
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '家常豆腐',
    '香辣下饭的家常豆腐，豆腐外焦里嫩。',
    'https://images.example.com/jiachang_doufu.jpg',
    'https://videos.example.com/jiachang_doufu.mp4',
    28, 2, 'medium', @cuisine_home,
    520.00, 32.00, 26.00, 30.00
);
SET @recipe_home_tofu := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_home_tofu, 1, '准备',
    '嫩豆腐切厚片入盐水焯烫，捞出沥干；猪肉切薄片，青椒胡萝卜切条。',
    6, '中火', JSON_ARRAY('砧板', '菜刀', '汤锅'),
    '焯烫可去豆腥并增强豆腐韧性。'
);
SET @step_home_tofu_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_home_tofu_1, @tool_board, '切块'),
    (@step_home_tofu_1, @tool_knife, '切片'),
    (@step_home_tofu_1, @tool_soup_pot, '焯烫');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_home_tofu, 2, '煎豆腐',
    '平底锅加少许油，将豆腐煎至两面金黄取出。',
    4, '中火', JSON_ARRAY('平底锅', '锅铲'),
    '煎制过程中轻推豆腐，避免粘锅。'
);
SET @step_home_tofu_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_home_tofu_2, @tool_flat_pan, '煎制'),
    (@step_home_tofu_2, @tool_spatula, '翻面');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_home_tofu, 3, '合炒',
    '热锅下油炒香豆瓣酱、蒜末，加入猪肉片翻炒变色，再放入豆腐、青椒、胡萝卜，加入酱油和少许水焖煮2分钟。',
    6, '中火', JSON_ARRAY('炒锅', '锅铲'),
    '翻动豆腐时动作轻，保持完整。'
);
SET @step_home_tofu_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_home_tofu_3, @tool_wok, '翻炒'),
    (@step_home_tofu_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_home_tofu, @ing_soft_tofu, '400', 'g', '切片焯烫', 4, 1, NULL, 280.00, 'main'),
    (@recipe_home_tofu, @ing_pork_loin, '120', 'g', '切片', 3, 0, NULL, 171.60, 'auxiliary'),
    (@recipe_home_tofu, @ing_green_pepper, '60', 'g', '切条', 2, 0, NULL, 12.00, 'auxiliary'),
    (@recipe_home_tofu, @ing_carrot, '50', 'g', '切条', 1, 0, NULL, 20.50, 'auxiliary'),
    (@recipe_home_tofu, @ing_douban, '15', 'g', '炒香', 1, 0, NULL, 27.75, 'seasoning'),
    (@recipe_home_tofu, @ing_garlic, '12', 'g', '切末', 1, 0, NULL, 17.88, 'seasoning'),
    (@recipe_home_tofu, @ing_soy_sauce, '18', 'ml', '调味', 0, 0, NULL, 12.96, 'seasoning'),
    (@recipe_home_tofu, @ing_cornstarch, '6', 'g', '勾芡', 0, 0, NULL, 22.86, 'seasoning'),
    (@recipe_home_tofu, @ing_salt, '3', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning'),
    (@recipe_home_tofu, @ing_cooking_oil, '18', 'g', '煎炒', 0, 0, NULL, 159.12, 'seasoning');

-- Recipe 20: 椒香虾仁
INSERT INTO recipes (
    name, description, image_url, video_url, total_time, servings, difficulty,
    cuisine_id, total_calories, total_protein, total_carbs, total_fat
) VALUES (
    '椒香虾仁',
    '椒麻清香的虾仁小炒，鲜嫩爽口。',
    'https://images.example.com/jiaoxiang_xiaren.jpg',
    'https://videos.example.com/jiaoxiang_xiaren.mp4',
    16, 2, 'easy', @cuisine_sichuan,
    300.00, 26.00, 10.00, 14.00
);
SET @recipe_pepper_shrimp := LAST_INSERT_ID();

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pepper_shrimp, 1, '腌制',
    '虾仁加入酱油、黑胡椒碎、淀粉抓匀腌制10分钟。',
    10, '常温', JSON_ARRAY('搅拌碗'),
    '腌制时加入少许香油提升香气。'
);
SET @step_pepper_shrimp_1 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pepper_shrimp_1, @tool_mix_bowl, '腌制');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pepper_shrimp, 2, '炝锅',
    '热锅下油，加入干辣椒与花椒小火炒香，再放入蒜姜末。',
    1, '中火', JSON_ARRAY('炒锅', '锅铲'),
    '炝锅时火力不宜过大，避免焦糊。'
);
SET @step_pepper_shrimp_2 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pepper_shrimp_2, @tool_wok, '炝锅'),
    (@step_pepper_shrimp_2, @tool_spatula, '翻动');

INSERT INTO recipe_steps (
    recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips
) VALUES (
    @recipe_pepper_shrimp, 3, '快炒',
    '倒入虾仁大火快炒至变色，加入酱油、香油、白砂糖调味，快速翻匀即可。',
    2, '大火', JSON_ARRAY('炒锅', '锅铲'),
    '炒制时间短，虾仁保持弹嫩。'
);
SET @step_pepper_shrimp_3 := LAST_INSERT_ID();

INSERT INTO step_tools (step_id, tool_id, usage) VALUES
    (@step_pepper_shrimp_3, @tool_wok, '翻炒'),
    (@step_pepper_shrimp_3, @tool_spatula, '翻炒');

INSERT INTO recipe_ingredients (
    recipe_id, ingredient_id, quantity, unit, prep_method, prep_time,
    is_main, substitute, adjusted_calories, ingredient_type
) VALUES
    (@recipe_pepper_shrimp, @ing_shrimp, '240', 'g', '腌制', 10, 1, NULL, 216.00, 'main'),
    (@recipe_pepper_shrimp, @ing_dried_chili, '6', 'g', '剪段', 1, 0, NULL, 9.00, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_sichuan_pepper, '3', 'g', '备用', 0, 0, NULL, 9.00, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_garlic, '10', 'g', '切末', 1, 0, NULL, 14.90, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_ginger, '8', 'g', '切末', 1, 0, NULL, 6.40, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_black_pepper, '4', 'g', '腌制', 0, 0, NULL, 10.20, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_soy_sauce, '12', 'ml', '调味', 0, 0, NULL, 8.64, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_sesame_oil, '6', 'ml', '调味', 0, 0, NULL, 53.04, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_cooking_oil, '16', 'g', '爆香', 0, 0, NULL, 141.44, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_sugar, '4', 'g', '调味', 0, 0, NULL, 15.48, 'seasoning'),
    (@recipe_pepper_shrimp, @ing_salt, '2', 'g', '调味', 0, 0, NULL, 0.00, 'seasoning');

COMMIT;

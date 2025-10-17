-- 菜谱管理系统模拟数据脚本
-- 插入示例菜谱、食材、步骤等数据

USE recipe_db;

-- 1. 插入菜系数据
INSERT INTO cuisines (name, cooking_style, typical_tools) VALUES
('川菜', '以麻辣鲜香为特色,善用辣椒、花椒等调料,烹饪技法多样', '["炒锅", "砂锅", "蒸笼"]'),
('粤菜', '清淡鲜美,注重原汁原味,擅长煲汤和蒸煮', '["蒸锅", "砂锅", "炒锅"]'),
('鲁菜', '口味咸鲜,善用葱姜蒜,注重火候掌控', '["炒锅", "砂锅", "刀具"]'),
('淮扬菜', '口味清淡,刀工精细,注重造型美观', '["刀具", "蒸笼", "炒锅"]');

-- 2. 插入食材数据
INSERT INTO ingredients (name, category, calories, protein, carbs, fat, storage_method, shelf_life) VALUES
-- 肉类-原料
('鸡胸肉', '肉类-原料', 165.00, 31.00, 0.00, 3.60, '冷藏', 3),
('鸡腿肉', '肉类-原料', 181.00, 25.00, 0.00, 9.00, '冷藏', 3),
('猪五花肉', '肉类-原料', 518.00, 9.30, 0.00, 53.00, '冷藏', 3),
('牛里脊', '肉类-原料', 125.00, 20.00, 0.00, 4.20, '冷藏', 3),
('虾仁', '海鲜-原料', 101.00, 20.60, 1.50, 1.20, '冷冻', 30),

-- 蔬菜-辅料
('青椒', '蔬菜-辅料', 22.00, 1.00, 4.90, 0.20, '常温', 5),
('红椒', '蔬菜-辅料', 20.00, 0.90, 4.60, 0.20, '常温', 5),
('洋葱', '蔬菜-辅料', 39.00, 1.00, 9.00, 0.10, '常温', 14),
('大葱', '蔬菜-辅料', 30.00, 1.50, 6.50, 0.30, '常温', 7),
('生姜', '蔬菜-辅料', 41.00, 1.80, 9.00, 0.70, '常温', 30),
('大蒜', '蔬菜-辅料', 128.00, 4.50, 27.60, 0.20, '常温', 30),
('花生', '坚果-辅料', 567.00, 24.80, 21.70, 48.70, '干燥', 180),
('黄瓜', '蔬菜-辅料', 15.00, 0.80, 3.00, 0.20, '冷藏', 7),

-- 调味-调料
('酱油', '调味-调料', 63.00, 5.60, 10.50, 0.00, '常温', 365),
('料酒', '调味-调料', 60.00, 0.20, 5.00, 0.00, '常温', 365),
('白糖', '调味-调料', 400.00, 0.00, 100.00, 0.00, '常温', 730),
('食盐', '调味-调料', 0.00, 0.00, 0.00, 0.00, '常温', 3650),
('食用油', '调味-调料', 900.00, 0.00, 0.00, 100.00, '常温', 365),
('辣椒酱', '调味-调料', 60.00, 2.00, 10.00, 1.50, '常温', 180),
('花椒', '调味-调料', 258.00, 6.70, 51.80, 8.90, '干燥', 365),
('蚝油', '调味-调料', 78.00, 1.90, 17.00, 0.10, '常温', 365),
('醋', '调味-调料', 31.00, 0.40, 7.20, 0.00, '常温', 730);

-- 3. 插入烹饪工具
INSERT INTO cooking_tools (name, type, material, capacity) VALUES
('炒锅', 'pan', '不粘涂层', '32cm'),
('蒸锅', 'pot', '不锈钢', '28cm'),
('砂锅', 'pot', '陶瓷', '2L'),
('菜刀', 'knife', '不锈钢', NULL),
('炖锅', 'pot', '不锈钢', '3L'),
('烤箱', 'oven', '电', '30L'),
('锅铲', 'other', '不锈钢', NULL),
('漏勺', 'other', '不锈钢', NULL);

-- 4. 插入菜谱: 宫保鸡丁
INSERT INTO recipes (name, description, image_url, video_url, total_time, servings, difficulty, cuisine_id, total_calories, total_protein, total_carbs, total_fat)
VALUES ('宫保鸡丁', '经典川菜,鸡肉鲜嫩,花生酥脆,麻辣鲜香,下饭佳肴',
        'https://example.com/gongbao.jpg', 'https://example.com/gongbao_video.mp4',
        35, 4, 'medium', 1, 450.50, 35.00, 25.00, 28.00);

-- 宫保鸡丁的食材
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, prep_method, prep_time, is_main, ingredient_type, adjusted_calories)
VALUES
-- 原料
(1, 1, '300', 'g', '切丁', 10, TRUE, 'main', 495.00),
-- 辅料
(1, 6, '100', 'g', '切块', 3, FALSE, 'auxiliary', 22.00),
(1, 7, '50', 'g', '切块', 3, FALSE, 'auxiliary', 10.00),
(1, 12, '80', 'g', '炒香', 5, FALSE, 'auxiliary', 453.60),
(1, 9, '20', 'g', '切段', 2, FALSE, 'auxiliary', 6.00),
(1, 10, '10', 'g', '切片', 2, FALSE, 'auxiliary', 4.10),
(1, 11, '15', 'g', '切末', 2, FALSE, 'auxiliary', 19.20),
-- 调料
(1, 14, '20', 'ml', NULL, 0, FALSE, 'seasoning', 12.60),
(1, 15, '10', 'ml', NULL, 0, FALSE, 'seasoning', 6.00),
(1, 16, '15', 'g', NULL, 0, FALSE, 'seasoning', 60.00),
(1, 18, '30', 'ml', NULL, 0, FALSE, 'seasoning', 270.00),
(1, 19, '10', 'g', NULL, 0, FALSE, 'seasoning', 25.80);

-- 宫保鸡丁的烹饪步骤
INSERT INTO recipe_steps (recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips)
VALUES
(1, 1, '腌制', '将鸡胸肉切成1.5cm小丁,加入料酒、少许盐、生抽腌制15分钟,让肉质更嫩滑', 15, '常温', '["菜刀"]', '腌制时间不宜过长,否则肉质发柴'),
(1, 2, '准备', '青椒红椒切块,大葱切段,姜蒜切末,花生米提前炒香备用', 8, NULL, '["菜刀"]', '蔬菜尽量切成大小均匀的块'),
(1, 3, '调酱', '碗中混合酱油、醋、白糖、料酒调成酱汁', 2, NULL, '[]', '可根据个人口味调整酱汁比例'),
(1, 4, '炒制', '热锅下油,中大火爆炒腌好的鸡丁至变色,盛出备用', 5, '大火', '["炒锅", "锅铲"]', '鸡丁不要炒太久,断生即可'),
(1, 5, '爆香', '锅中留底油,下花椒粒爆香,再加入干辣椒、姜蒜末炒出香味', 3, '中火', '["炒锅", "锅铲"]', '花椒不要炒糊,避免发苦'),
(1, 6, '翻炒', '倒入青红椒块翻炒1分钟,再倒回鸡丁,淋入调好的酱汁快速翻炒均匀', 2, '大火', '["炒锅", "锅铲"]', '大火快炒保持食材脆嫩'),
(1, 7, '出锅', '最后加入炒香的花生米,翻炒均匀即可出锅', 1, '大火', '["炒锅", "锅铲"]', '花生米最后加入,保持酥脆口感');

-- 步骤-工具关联
INSERT INTO step_tools (step_id, tool_id, usage) VALUES
(1, 4, '切配工具'),
(2, 4, '切配工具'),
(4, 1, '主烹饪锅'),
(4, 7, '翻炒工具'),
(5, 1, '主烹饪锅'),
(5, 7, '翻炒工具'),
(6, 1, '主烹饪锅'),
(6, 7, '翻炒工具'),
(7, 1, '主烹饪锅'),
(7, 7, '翻炒工具');

-- 5. 插入菜谱: 清蒸鲈鱼
INSERT INTO recipes (name, description, image_url, video_url, total_time, servings, difficulty, cuisine_id, total_calories, total_protein, total_carbs, total_fat)
VALUES ('清蒸鲈鱼', '粤菜经典,鱼肉鲜嫩,清淡爽口,营养丰富',
        'https://example.com/steamed_fish.jpg', NULL,
        25, 3, 'easy', 2, 280.00, 42.00, 8.00, 12.00);

-- 清蒸鲈鱼的食材 (简化示例)
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, prep_method, prep_time, is_main, ingredient_type, adjusted_calories)
VALUES
-- 原料: 鲈鱼 (这里用虾仁代替演示)
(2, 5, '500', 'g', '清洗处理', 15, TRUE, 'main', 505.00),
-- 辅料
(2, 9, '30', 'g', '切丝', 3, FALSE, 'auxiliary', 9.00),
(2, 10, '20', 'g', '切丝', 2, FALSE, 'auxiliary', 8.20),
-- 调料
(2, 14, '30', 'ml', NULL, 0, FALSE, 'seasoning', 18.90),
(2, 18, '20', 'ml', NULL, 0, FALSE, 'seasoning', 180.00);

-- 清蒸鲈鱼的步骤
INSERT INTO recipe_steps (recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips)
VALUES
(2, 1, '处理', '鱼洗净,两面划几刀,用料酒和盐抹匀腌制10分钟', 10, '常温', '["菜刀"]', '划刀深度约1cm,便于入味'),
(2, 2, '蒸制', '鱼放入蒸锅,大火蒸8-10分钟至熟透', 10, '大火', '["蒸锅"]', '时间根据鱼大小调整'),
(2, 3, '调味', '蒸好后倒掉盘中汤汁,摆上葱姜丝,淋热油激发香味', 3, NULL, '["炒锅"]', '油要烧至冒烟'),
(2, 4, '出锅', '最后淋上蒸鱼豉油即可', 1, NULL, '[]', '也可用生抽代替');

-- 步骤-工具关联
INSERT INTO step_tools (step_id, tool_id, usage) VALUES
(8, 4, '处理工具'),
(9, 2, '主蒸锅'),
(10, 1, '热油锅');

-- 6. 插入菜谱: 红烧肉
INSERT INTO recipes (name, description, image_url, video_url, total_time, servings, difficulty, cuisine_id, total_calories, total_protein, total_carbs, total_fat)
VALUES ('红烧肉', '色泽红亮,肥而不腻,入口即化的经典家常菜',
        'https://example.com/hongshaorou.jpg', 'https://example.com/hongshaorou_video.mp4',
        90, 4, 'medium', 3, 650.00, 15.00, 35.00, 55.00);

-- 红烧肉的食材
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, prep_method, prep_time, is_main, ingredient_type, adjusted_calories)
VALUES
-- 原料
(3, 3, '600', 'g', '切块', 10, TRUE, 'main', 3108.00),
-- 辅料
(3, 9, '50', 'g', '切段', 3, FALSE, 'auxiliary', 15.00),
(3, 10, '30', 'g', '切片', 2, FALSE, 'auxiliary', 12.30),
-- 调料
(3, 14, '40', 'ml', NULL, 0, FALSE, 'seasoning', 25.20),
(3, 15, '30', 'ml', NULL, 0, FALSE, 'seasoning', 18.00),
(3, 16, '40', 'g', NULL, 0, FALSE, 'seasoning', 160.00),
(3, 18, '30', 'ml', NULL, 0, FALSE, 'seasoning', 270.00);

-- 红烧肉的步骤
INSERT INTO recipe_steps (recipe_id, step_number, action, instruction, duration, temperature, tools_used, tips)
VALUES
(3, 1, '焯水', '五花肉冷水下锅,加料酒和姜片,焯水去腥,捞出洗净', 10, '大火', '["炖锅"]', '要冷水下锅,热水下锅肉质会收缩'),
(3, 2, '炒糖色', '锅中放少许油和冰糖,小火炒至糖色枣红', 8, '小火', '["炒锅", "锅铲"]', '火候很重要,炒过头会发苦'),
(3, 3, '上色', '倒入焯好的五花肉块,快速翻炒上色', 5, '中火', '["炒锅", "锅铲"]', '均匀裹上糖色'),
(3, 4, '调味', '加入酱油、料酒、葱姜,倒入开水没过肉', 3, NULL, '["炒锅"]', '一定要加开水,冷水会让肉质变硬'),
(3, 5, '炖煮', '转入砂锅,大火烧开后转小火炖60分钟', 60, '小火', '["砂锅"]', '中途可以翻动几次,让上色更均匀'),
(3, 6, '收汁', '转大火收汁至浓稠,期间不停翻炒', 8, '大火', '["砂锅", "锅铲"]', '不要收太干,留些汁水拌饭更香'),
(3, 7, '出锅', '出锅装盘,撒上葱花点缀', 1, NULL, '[]', '');

-- 步骤-工具关联
INSERT INTO step_tools (step_id, tool_id, usage) VALUES
(11, 5, '焯水锅'),
(12, 1, '炒制锅'),
(12, 7, '翻炒'),
(13, 1, '炒制锅'),
(13, 7, '翻炒'),
(14, 1, '调味锅'),
(15, 3, '炖煮锅'),
(16, 3, '收汁锅'),
(16, 7, '翻炒');

-- 数据插入完成
SELECT 'MySQL 模拟数据插入完成!' AS message;
SELECT '共插入:' AS info,
       (SELECT COUNT(*) FROM cuisines) AS '菜系数',
       (SELECT COUNT(*) FROM ingredients) AS '食材数',
       (SELECT COUNT(*) FROM recipes) AS '菜谱数',
       (SELECT COUNT(*) FROM recipe_steps) AS '步骤数',
       (SELECT COUNT(*) FROM cooking_tools) AS '工具数';

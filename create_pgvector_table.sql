-- 创建pgvector表
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建历史菜谱向量表
DROP TABLE IF EXISTS historical_recipes_vector;
CREATE TABLE historical_recipes_vector (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100),
    source_id VARCHAR(100),
    dish_name VARCHAR(200),
    dynasty VARCHAR(50),
    region VARCHAR(100),
    historical_content TEXT,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引
CREATE INDEX idx_historical_recipes_embedding ON historical_recipes_vector
USING ivfflat (embedding vector_cosine_ops);

-- 插入一些示例数据（使用随机向量作为占位符）
INSERT INTO historical_recipes_vector (source_table, source_id, dish_name, dynasty, region, historical_content, embedding)
VALUES
('Sheet1', '0', '红烧肉', '宋代', '浙江', '红烧肉 - 起源于宋代，苏东坡在黄州时期创制 - 宋代 - 浙江 - 创始人: 苏东坡 - 历史故事: 苏东坡被贬黄州，当地猪肉便宜，他用慢火炖制，创造了这道名菜', '[0.1,0.2,0.3]'),
('Sheet1', '1', '宫保鸡丁', '清代', '四川', '宫保鸡丁 - 清代宫廷菜，由宫保丁宝桢所创 - 清代 - 四川 - 创始人: 丁宝桢 - 历史故事: 丁宝桢在四川总督任上，喜食辣鸡丁，厨师以此命名', '[0.2,0.3,0.4]'),
('Sheet1', '2', '麻婆豆腐', '清代', '四川', '麻婆豆腐 - 清代同治年间，成都陈麻婆豆腐店创制 - 清代 - 四川 - 创始人: 陈麻婆 - 历史故事: 陈麻婆本是成都店主，擅做豆腐，麻辣鲜香独具特色', '[0.3,0.4,0.5]');

-- 验证插入
SELECT COUNT(*) as total_records FROM historical_recipes_vector;
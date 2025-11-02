-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建可搜索的文档表
CREATE TABLE IF NOT EXISTS searchable_documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255),
    source VARCHAR(255),
    content TEXT,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_searchable_documents_embedding ON searchable_documents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_searchable_documents_source ON searchable_documents(source);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
DROP TRIGGER IF EXISTS update_searchable_documents_updated_at ON searchable_documents;
CREATE TRIGGER update_searchable_documents_updated_at
    BEFORE UPDATE ON searchable_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 输出完成信息
SELECT 'pgvector extension and tables initialized successfully' AS status;
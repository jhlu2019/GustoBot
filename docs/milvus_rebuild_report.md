# Milvus 重建报告

## 重建时间
2025-11-02 14:03

## 重建原因
原始 Milvus 集合配置为 4096 维 embedding，但实际使用的 embedding 是 1024 维，导致维度不匹配错误：
```
Collection field dim is 4096, but entities field dim is 1024
```

## 重建步骤

### 1. 停止 Milvus 相关服务
```bash
docker-compose stop milvus etcd minio
```

### 2. 删除容器和数据卷
```bash
docker-compose rm -f milvus etcd minio
docker volume rm gustobot_milvus_data gustobot_etcd_data gustobot_minio_data
```

### 3. 重新启动服务
```bash
docker-compose up -d etcd minio milvus
```

### 4. 清理旧集合
```bash
curl -X DELETE "http://localhost:8000/api/v1/knowledge/clear?confirm=true"
```

## 验证结果

### ✅ 服务状态
- Milvus: 运行正常 (端口 19530)
- Etcd: 运行正常
- Minio: 运行正常 (健康状态)

### ✅ 连接测试
- Backend 成功连接到 Milvus
- 创建新集合: `recipes`
- 使用正确的 1024 维 embedding

### ✅ 数据导入测试
成功添加测试菜谱（宫保鸡丁）：
- Recipe ID: `recipe_bb86d381`
- 状态: 201 Created
- 无维度错误

### ✅ 查询测试
直接知识库搜索成功：
- 找到 1 个结果
- 相似度分数: 0.659
- Rerank 分数: 0.834

## 系统现状

### 路由行为
- 关于菜谱做法的问题被路由到 `graphrag-query` (Neo4j)
- 这是正常行为，因为结构化的菜谱信息更适合知识图谱查询
- `kb-query` 路由仍然正常工作，用于更广泛的知识检索

### 数据状态
- Milvus: 空集合 → 已添加 1 条测试数据
- PostgreSQL: 仍然为空（需要单独配置）
- Neo4j: 包含预加载的菜谱知识图谱

## 后续建议

1. **批量导入数据**
   - 使用 `/api/v1/knowledge/recipes/batch` 批量导入菜谱
   - 或配置 kb_ingest 服务进行自动化导入

2. **PostgreSQL 配置**
   - 配置 kb_ingest 服务的环境变量
   - 启用结构化数据存储功能

3. **测试更多查询类型**
   - 测试历史、文化等知识性问题（真正使用 kb-query）
   - 验证不同路由的工作效果

## 结论

Milvus 重建成功，维度不匹配问题已解决。知识库基础功能正常，可以继续进行数据导入和功能测试。
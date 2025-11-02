# KB-Query 数据状态调查报告

## 调查时间
2025-11-02

## 调查结果

### 1. PostgreSQL (kb_postgres) - 无数据 ❌
- **状态**: 数据库 `vector_db` 存在但完全为空
- **表数量**: 0 个表
- **数据**: 无

```sql
-- 查询结果
postgres=# \dt
Did not find any relations.
```

### 2. Milvus 向量库 - 有结构无数据 ❌
- **状态**: `recipes` 集合已创建
- **数据条数**: 0 条
- **问题**: embedding维度不匹配
  - 集合配置维度: 4096
  - 实际embedding维度: 1024
  - 错误信息: `Collection field dim is 4096, but entities field dim is 1024`

### 3. kb_ingest 服务 - 配置问题 ❌
- **状态**: 服务运行但无法处理请求
- **缺少的配置**:
  - `KB_EMBEDDING_API_KEY`
  - `KB_EMBEDDING_BASE_URL`
  - `KB_EMBEDDING_MODEL`
  - `KB_LLM_*` 相关配置

## 问题分析

### 根本原因
1. **数据从未导入**: PostgreSQL和Milvus都是空的
2. **维度不匹配**: Milvus集合是为4096维embedding创建的，但当前使用的是1024维
3. **服务配置缺失**: kb_ingest服务缺少必要的环境变量

### 为什么会这样？
- Milvus集合可能是在旧版本配置下创建的（当时使用4096维embedding）
- 后来配置改为1024维但没有重建Milvus集合
- kb_ingest服务的环境变量（KB_*）未设置

## 解决方案

### 方案1: 重建Milvus集合
```bash
# 1. 停止服务
docker-compose down milvus

# 2. 删除Milvus数据
docker volume rm gustobot_milvus_data

# 3. 重新启动
docker-compose up -d milvus
```

### 方案2: 更新环境变量
在 `.env` 文件中添加：
```env
# kb_ingest 服务配置
KB_EMBEDDING_API_KEY=your_embedding_api_key
KB_EMBEDDING_BASE_URL=your_embedding_base_url
KB_EMBEDDING_MODEL=text-embedding-v4
KB_LLM_API_KEY=your_llm_api_key
KB_LLM_BASE_URL=your_llm_base_url
KB_LLM_MODEL=your_llm_model
```

### 方案3: 导入测试数据
1. 先修复配置问题
2. 使用批量导入API导入基础菜谱数据
3. 验证数据是否正确存储

## 当前状态总结

| 组件 | 数据状态 | 主要问题 |
|------|----------|----------|
| PostgreSQL | 空 | 无表无数据 |
| Milvus | 空集合 | 维度不匹配 |
| kb_ingest | 运行但无法工作 | 缺少环境变量 |

## KB-Query 为什么返回空结果

1. **路由正确**: 系统正确识别为 `kb-query`
2. **查询失败**:
   - 首先尝试PostgreSQL → 空表
   - Fallback到Milvus → 维度不匹配导致查询失败
3. **最终结果**: 返回"暂未找到相关记载"

## 建议

1. **优先修复kb_ingest配置** - 添加必要的环境变量
2. **重建Milvus集合** - 使用正确的embedding维度（1024）
3. **导入基础数据** - 至少导入一些常用的菜谱数据
4. **验证端到端流程** - 确保kb-query能正常工作

## 结论

kb-query路由系统本身是**正常工作**的，问题出在数据存储层：
- PostgreSQL空库
- Milvus配置错误
- kb_ingest服务配置不完整

修复这些问题后，kb-query应该能正常返回知识库内容。
# 智能体架构重构说明

## 重构概述

本次重构将原来的 `agent_service.py` 文件（1365行）拆分为多个模块化的文件，提高了代码的可维护性、可测试性和可扩展性。

## 新的目录结构

```
backend/app/agents/
├── __init__.py              # 模块导出
├── README.md               # 本文档
├── types.py                # 类型定义和常量
├── base.py                 # 基础智能体类和工具
├── factory.py              # 智能体工厂
├── schema_retriever.py     # 表结构检索智能体
├── query_analyzer.py       # 查询分析智能体
├── sql_generator.py        # SQL生成智能体
├── sql_explainer.py        # SQL解释智能体
├── sql_executor.py         # SQL执行智能体
└── visualization_recommender.py  # 可视化推荐智能体

backend/app/services/
├── agent_orchestrator.py   # 智能体编排服务
└── agent_service.py        # 重构后的兼容接口
```

## 重构优势

### 1. 模块化设计
- 每个智能体独立成文件，职责清晰
- 便于单独测试和维护
- 降低代码耦合度

### 2. 可维护性提升
- 代码结构清晰，易于理解
- 修改一个智能体不会影响其他智能体
- 便于新增或删除智能体

### 3. 可测试性改善
- 每个智能体可以独立进行单元测试
- 模拟依赖更加容易
- 测试覆盖率更容易提升

### 4. 可扩展性增强
- 新增智能体只需创建新文件并在工厂中注册
- 支持插件化架构
- 便于实现不同的智能体策略

## 核心组件说明

### BaseAgent (base.py)
- 所有智能体的基类
- 提供通用功能：错误处理、消息发送、表结构格式化等
- 包含StreamResponseCollector用于流式响应处理

### AgentFactory (factory.py)
- 智能体工厂模式实现
- 统一管理智能体的创建和注册
- 支持根据配置选择不同的智能体实现

### AgentOrchestrator (agent_orchestrator.py)
- 智能体编排服务
- 管理智能体的生命周期
- 处理数据库连接和配置

### 各个智能体
每个智能体都继承自BaseAgent，实现特定的功能：
- **SchemaRetrieverAgent**: 从图数据库获取相关表结构
- **QueryAnalyzerAgent**: 分析用户查询意图
- **SqlGeneratorAgent**: 生成SQL语句
- **SqlExplainerAgent**: 解释SQL语句含义
- **SqlExecutorAgent**: 执行SQL查询
- **VisualizationRecommenderAgent**: 推荐可视化方案

## 向后兼容性

重构后的 `agent_service.py` 保持了向后兼容性：
- 保留了原有的导出接口
- 主题类型常量保持不变
- Text2SQLService接口保持一致

## 使用方式

### 直接使用新架构
```python
from app.agents import AgentFactory, StreamResponseCollector
from app.services.agent_orchestrator import AgentOrchestrator

# 创建编排器
orchestrator = AgentOrchestrator()

# 处理查询
await orchestrator.process_query(query, collector, connection_id)
```

### 使用兼容接口
```python
from app.services.agent_service import Text2SQLService

# 保持原有使用方式
service = Text2SQLService()
await service.process_query(query, collector, connection_id)
```

## 配置支持

支持通过配置选择不同的智能体实现：
- `HYBRID_RETRIEVAL_ENABLED`: 是否启用混合检索增强的SQL生成智能体
- 其他配置项可在 `app.core.config` 中定义

## 测试建议

1. **单元测试**: 为每个智能体编写独立的单元测试
2. **集成测试**: 测试智能体之间的协作
3. **端到端测试**: 测试完整的查询处理流程

## 未来扩展

1. **插件系统**: 支持动态加载智能体插件
2. **配置化**: 通过配置文件定义智能体流程
3. **监控和日志**: 增加智能体执行监控和详细日志
4. **性能优化**: 智能体并行执行和缓存机制

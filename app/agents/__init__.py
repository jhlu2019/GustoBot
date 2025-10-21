"""
Multi-Agent System
Language Graph Agent Package
多智能体系统核心模块

新架构 (推荐):
- supervisor_agent_v2.SupervisorAgent: 使用 TypedDict 和纯函数节点
- nodes: 所有纯函数节点实现
- state_models: TypedDict 状态定义

旧架构 (保留):
- supervisor_agent.SupervisorAgent: 旧版类式实现
- router_agent, knowledge_agent, chat_agent: 旧版类式 Agent
"""


# 新增组件
from . import kb_tools, crawler

__all__ = [

    # 组件模块
    "kb_tools",
    "crawler",
]

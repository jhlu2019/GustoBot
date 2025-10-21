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
from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .knowledge_agent import KnowledgeAgent
from .chat_agent import ChatAgent
from .supervisor_agent import SupervisorAgent

# 新架构导出 (推荐使用)
from .supervisor_agent_v2 import SupervisorAgent as SupervisorAgentV2
from . import nodes
from .state_models import ConversationState, ConversationInput, RouterResult, AgentAnswer

# 新增组件
from . import kb, crawler

__all__ = [
    # 旧架构 (向后兼容)
    "BaseAgent",
    "RouterAgent",
    "KnowledgeAgent",
    "ChatAgent",
    "SupervisorAgent",

    # 新架构 (推荐)
    "SupervisorAgentV2",
    "nodes",
    "ConversationState",
    "ConversationInput",
    "RouterResult",
    "AgentAnswer",

    # 组件模块
    "kb",
    "crawler",
]

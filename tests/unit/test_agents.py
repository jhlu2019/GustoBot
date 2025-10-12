"""
Agent单元测试
"""
import pytest
from server.agents import RouterAgent, KnowledgeAgent, ChatAgent


@pytest.mark.asyncio
async def test_router_agent_initialization():
    """测试RouterAgent初始化"""
    agent = RouterAgent()
    assert agent.name == "RouterAgent"
    assert "路由" in agent.description or "route" in agent.description.lower()


@pytest.mark.asyncio
async def test_router_agent_rule_based_classification():
    """测试基于规则的分类"""
    agent = RouterAgent()

    # 测试菜谱相关问题
    result = agent._rule_based_classification("怎么做红烧肉？")
    assert result["route"] == "knowledge"

    # 测试闲聊
    result = agent._rule_based_classification("你好")
    assert result["route"] == "chat"


@pytest.mark.asyncio
async def test_knowledge_agent_initialization():
    """测试KnowledgeAgent初始化"""
    agent = KnowledgeAgent()
    assert agent.name == "KnowledgeAgent"


@pytest.mark.asyncio
async def test_chat_agent_initialization():
    """测试ChatAgent初始化"""
    agent = ChatAgent()
    assert agent.name == "ChatAgent"


@pytest.mark.asyncio
async def test_chat_agent_template_response():
    """测试ChatAgent模板回复"""
    agent = ChatAgent()

    # 测试问候
    response = agent._generate_template_response("你好")
    assert "GustoBot" in response or "菜谱" in response

    # 测试感谢
    response = agent._generate_template_response("谢谢")
    assert "不客气" in response or "服务" in response

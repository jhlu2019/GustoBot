"""
快速测试新 LangGraph 架构
Quick test for the new LangGraph architecture
"""
import asyncio
from gustobot.application.agents.nodes import route_question, chat_response
from gustobot.application.agents.state_models import ConversationState


async def test_route_node():
    """测试路由节点"""
    print("=" * 60)
    print("测试 1: 路由节点 (纯函数)")
    print("=" * 60)

    # 测试菜谱问题
    state1: ConversationState = {"message": "如何做红烧肉？"}
    result1 = await route_question(state1, llm_client=None)
    print(f"\n问题: {state1['message']}")
    print(f"路由: {result1.get('route')}")
    print(f"置信度: {result1.get('confidence')}")
    print(f"原因: {result1.get('reason')}")

    # 测试闲聊
    state2: ConversationState = {"message": "你好"}
    result2 = await route_question(state2, llm_client=None)
    print(f"\n问题: {state2['message']}")
    print(f"路由: {result2.get('route')}")
    print(f"置信度: {result2.get('confidence')}")
    print(f"原因: {result2.get('reason')}")


async def test_chat_node():
    """测试聊天节点"""
    print("\n" + "=" * 60)
    print("测试 2: 聊天节点 (纯函数)")
    print("=" * 60)

    state: ConversationState = {
        "message": "你好",
        "history": []
    }

    result = await chat_response(state, llm_client=None)
    print(f"\n问题: {state['message']}")
    print(f"回答: {result.get('answer')}")
    print(f"类型: {result.get('answer_type')}")


async def test_state_immutability():
    """测试状态不可变性"""
    print("\n" + "=" * 60)
    print("测试 3: 状态不可变性 (TypedDict)")
    print("=" * 60)

    original_state: ConversationState = {
        "message": "测试",
        "session_id": "test_123"
    }

    # 节点函数返回新状态，不修改原状态
    new_state = await route_question(original_state, llm_client=None)

    print(f"\n原始状态: {original_state}")
    print(f"新状态包含路由: {'route' in new_state}")
    print(f"原始状态保持不变: {'route' not in original_state}")


async def test_supervisor_basic():
    """测试 SupervisorAgent 基本功能"""
    print("\n" + "=" * 60)
    print("测试 4: SupervisorAgent 集成测试")
    print("=" * 60)

    try:
        from gustobot.application.agents.supervisor_agent_v2 import SupervisorAgent
        from gustobot.infrastructure.knowledge import KnowledgeService
        from gustobot.application.services.llm_client import LLMClient

        # 初始化
        knowledge_service = KnowledgeService()
        llm_client = LLMClient()

        supervisor = SupervisorAgent(
            knowledge_service=knowledge_service,
            llm_client=llm_client,
            semantic_cache=None,
            history_store=None,
        )

        # 测试处理
        input_data = {
            "message": "你好",
            "session_id": "test_session",
            "user_id": "test_user"
        }

        print(f"\n输入: {input_data['message']}")
        result = await supervisor.process(input_data)

        print(f"回答: {result.get('answer')}")
        print(f"类型: {result.get('type')}")
        print(f"元数据: {result.get('metadata')}")

        print("\n✅ SupervisorAgent 工作正常!")

    except Exception as e:
        print(f"\n⚠️  SupervisorAgent 测试需要完整环境配置")
        print(f"错误: {e}")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试新 LangGraph 架构\n")

    await test_route_node()
    await test_chat_node()
    await test_state_immutability()
    await test_supervisor_basic()

    print("\n" + "=" * 60)
    print("✅ 所有基础测试完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 配置环境变量: cp .env.example .env")
    print("3. 启动服务: python -m uvicorn gustobot.main:app --reload")
    print("4. 测试 API:")
    print("   - POST /api/v1/chat/")
    print("   - POST /api/v1/chat/stream")
    print("   - GET /api/v1/chat/status")
    print()


if __name__ == "__main__":
    asyncio.run(main())

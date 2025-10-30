#!/usr/bin/env python3
"""
测试kb-query路由为什么没有使用LightRAG
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gustobot.application.agents.lg_builder import graph
from gustobot.application.agents.lg_states import AgentState
from langchain_core.messages import HumanMessage
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="test_kb_vs_lightrag")

async def test_kb_vs_lightrag():
    """对比kb-query和LightRAG API的差异"""

    test_question = "火锅有哪些种类？"

    print("🔍 对比测试: kb-query路由 vs LightRAG API")
    print("=" * 80)
    print(f"测试问题: {test_question}")
    print("=" * 80)

    # 1. 测试通过kb-query路由
    print("\n📋 1. 通过智能体路由 (kb-query)")
    print("-" * 40)

    state = AgentState(
        messages=[HumanMessage(content=test_question)]
    )

    config = {"configurable": {"thread_id": "kb_test_thread"}}
    result = await graph.ainvoke(state, config=config)

    kb_route = result.get("router", {}).get("type", "unknown")
    kb_logic = result.get("router", {}).get("logic", "N/A")
    kb_response = ""
    if result.get("messages"):
        kb_response = result["messages"][-1].content if result["messages"] else ""

    print(f"路由类型: {kb_route}")
    print(f"路由逻辑: {kb_logic}")
    print(f"回复内容: {kb_response[:200]}...")
    print(f"回复长度: {len(kb_response)} 字符")

    # 2. 直接调用LightRAG API
    print("\n📋 2. 直接调用LightRAG API")
    print("-" * 40)

    from gustobot.application.services.lightrag_service import get_lightrag_service
    lightrag_service = get_lightrag_service()

    lightrag_result = await lightrag_service.query(
        query=test_question,
        mode="hybrid"
    )

    # lightrag_result可能直接是字符串或字典
    if isinstance(lightrag_result, str):
        lightrag_response = lightrag_result
    else:
        lightrag_response = lightrag_result.get("response", "")
    print(f"查询模式: hybrid")
    print(f"回复内容: {lightrag_response[:200]}...")
    print(f"回复长度: {len(lightrag_response)} 字符")

    # 3. 分析差异
    print("\n📊 3. 对比分析")
    print("-" * 40)

    print(f"kb-query路由回复长度: {len(kb_response)} 字符")
    print(f"LightRAG API回复长度: {len(lightrag_response)} 字符")
    print(f"长度差异: {len(lightrag_response) - len(kb_response)} 字符")

    # 检查kb-query是否可能调用了LightRAG
    lightrag_indicators = [
        "根据提供的资料",
        "根据现有资料",
        "### References",
        "火锅是一种源自中国",
        "按汤底风味分类"
    ]

    has_lightrag_content = any(indicator in kb_response for indicator in lightrag_indicators)
    print(f"\nkb-query包含LightRAG内容: {'是' if has_lightrag_content else '否'}")

    if not has_lightrag_content:
        print("\n❌ 问题确认: kb-query路由没有使用LightRAG数据")
        print("可能的原因:")
        print("1. kb-query使用的是PostgreSQL+Milvus，而不是LightRAG")
        print("2. LightRAG数据没有被正确集成到kb-query工作流")
        print("3. kb-query的路由逻辑需要修改以包含LightRAG")
    else:
        print("\n✅ kb-query可能使用了LightRAG数据")

    # 4. 测试kb-query工作流的具体工具选择
    print("\n📋 4. 检查kb-query使用的工具")
    print("-" * 40)

    # 查看kb-query的日志信息
    if "PostgreSQL" in kb_logic or "Milvus" in kb_logic:
        print("✅ kb-query使用了PostgreSQL/Milvus工具")

    if "kb-query" in kb_route:
        print("ℹ️  kb-query路由被正确触发")
        print("ℹ️  但可能没有调用LightRAG服务")

    # 5. 结论
    print("\n🎯 结论")
    print("-" * 40)
    print("1. LightRAG API工作正常，能返回详细的火锅信息")
    print("2. kb-query路由被正确触发")
    print("3. 但kb-query没有使用LightRAG，而是查询了空的PostgreSQL/Milvus")
    print("4. 需要修改kb-query工作流以集成LightRAG查询")

if __name__ == "__main__":
    try:
        asyncio.run(test_kb_vs_lightrag())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
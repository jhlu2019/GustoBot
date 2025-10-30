#!/usr/bin/env python3
"""
测试智能体路由功能
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

logger = get_logger(service="test_agents")

# 测试用例
TEST_CASES = [
    # General-Query 测试
    {
        "question": "你好",
        "expected_route": "general-query",
        "description": "问候语测试"
    },
    {
        "question": "谢谢",
        "expected_route": "general-query",
        "description": "礼貌用语测试"
    },
    {
        "question": "今天天气真好",
        "expected_route": "general-query",
        "description": "闲聊测试"
    },

    # Additional-Query 测试
    {
        "question": "我想做菜",
        "expected_route": "additional-query",
        "description": "模糊提问需要补充信息"
    },
    {
        "question": "怎么做好吃的",
        "expected_route": "additional-query",
        "description": "缺少具体菜名"
    },

    # KB-Query 测试
    {
        "question": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query",
        "description": "菜谱历史典故查询"
    },
    {
        "question": "川菜的特点和历史背景",
        "expected_route": "kb-query",
        "description": "地域流派介绍"
    },

    # GraphRAG-Query 测试
    {
        "question": "红烧肉怎么做",
        "expected_route": "graphrag-query",
        "description": "菜谱做法查询"
    },
    {
        "question": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query",
        "description": "食材查询"
    },

    # Text2SQL-Query 测试
    {
        "question": "数据库里有多少道菜",
        "expected_route": "text2sql-query",
        "description": "统计查询"
    },
    {
        "question": "哪个菜系的菜谱最多",
        "expected_route": "text2sql-query",
        "description": "排名查询"
    }
]

async def test_single_agent_routing(question: str, expected_route: str, description: str):
    """测试单个问题的路由"""
    try:
        print(f"\n🧪 测试: {description}")
        print(f"❓ 问题: {question}")
        print(f"🎯 预期路由: {expected_route}")

        # 创建AgentState
        state = AgentState(
            messages=[HumanMessage(content=question)]
        )

        # 执行路由
        config = {"configurable": {"thread_id": "test_thread"}}
        start_time = asyncio.get_event_loop().time()
        result = await graph.ainvoke(state, config=config)
        elapsed_time = asyncio.get_event_loop().time() - start_time

        # 获取实际路由
        actual_route = result.get("router", {}).get("type", "unknown")
        logic = result.get("router", {}).get("logic", "N/A")

        # 获取回复内容
        response = ""
        if result.get("messages"):
            response = result["messages"][-1].content if result["messages"] else ""

        print(f"✅ 实际路由: {actual_route}")
        print(f"⏱️  响应时间: {elapsed_time:.2f}s")
        print(f"💬 回复前200字: {response[:200]}...")

        # 检查是否匹配
        is_match = actual_route == expected_route
        status = "✅ PASS" if is_match else "❌ FAIL"
        print(f"📊 状态: {status}")

        return {
            "question": question,
            "description": description,
            "expected_route": expected_route,
            "actual_route": actual_route,
            "is_match": is_match,
            "response_time": elapsed_time,
            "response": response[:500],
            "logic": logic
        }

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return {
            "question": question,
            "description": description,
            "expected_route": expected_route,
            "actual_route": "ERROR",
            "is_match": False,
            "error": str(e),
            "response_time": 0
        }

async def main():
    """主测试函数"""
    print("🚀 开始测试智能体路由功能")
    print("=" * 80)

    results = []
    passed = 0
    failed = 0

    for test_case in TEST_CASES:
        result = await test_single_agent_routing(
            test_case["question"],
            test_case["expected_route"],
            test_case["description"]
        )
        results.append(result)

        if result["is_match"]:
            passed += 1
        else:
            failed += 1

    # 统计结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    print(f"总测试数: {len(results)}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"成功率: {passed/len(results)*100:.1f}%")

    # 显示失败的测试
    if failed > 0:
        print("\n❌ 失败的测试用例:")
        for result in results:
            if not result["is_match"]:
                print(f"  • {result['description']}")
                print(f"    问题: {result['question']}")
                print(f"    预期: {result['expected_route']}")
                print(f"    实际: {result['actual_route']}")
                print()

    print("🎉 测试完成!")
    return results

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python3
"""
测试LightRAG的图查询功能是否正常工作
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

logger = get_logger(service="test_lightrag_graph")

# 专门测试LightRAG图查询的测试用例
LIGHTRAG_GRAPH_TESTS = [
    {
        "question": "火锅有哪些种类？",
        "expected_route": "kb-query",
        "description": "测试LightRAG查询火锅种类（应该使用历史数据）",
        "should_use_lightrag": True,
        "expected_keywords": ["火锅", "种类", "麻辣", "清汤", "鸳鸯"]
    },
    {
        "question": "请介绍一下四川火锅的特点",
        "expected_route": "kb-query",
        "description": "测试LightRAG查询火锅特点（应该使用LightRAG数据）",
        "should_use_lightrag": True,
        "expected_keywords": ["四川", "火锅", "麻辣", "特点", "风味"]
    },
    {
        "question": "火锅蘸料有哪些？",
        "expected_route": "kb-query",
        "description": "测试LightRAG查询蘸料信息",
        "should_use_lightrag": True,
        "expected_keywords": ["蘸料", "芝麻", "蒜泥", "辣椒油"]
    },
    {
        "question": "鸳鸯火锅的组成是什么？",
        "expected_route": "kb-query",
        "description": "测试LightRAG具体查询",
        "should_use_lightrag": True,
        "expected_keywords": ["鸳鸯", "清汤", "麻辣", "一半"]
    }
]

async def test_lightrag_graph_query(test_case: dict):
    """测试LightRAG图查询"""
    try:
        print(f"\n🧪 {test_case['description']}")
        print(f"❓ 问题: {test_case['question']}")
        print(f"🎯 预期路由: {test_case['expected_route']}")
        print(f"🔍 应该使用LightRAG: {test_case['should_use_lightrag']}")

        # 创建AgentState
        state = AgentState(
            messages=[HumanMessage(content=test_case['question'])]
        )

        # 执行路由
        config = {"configurable": {"thread_id": "lightrag_test_thread"}}
        start_time = asyncio.get_event_loop().time()
        result = await graph.ainvoke(state, config=config)
        elapsed_time = asyncio.get_event_loop().time() - start_time

        # 获取实际路由和回复
        actual_route = result.get("router", {}).get("type", "unknown")
        logic = result.get("router", {}).get("logic", "N/A")
        response = ""
        if result.get("messages"):
            response = result["messages"][-1].content if result["messages"] else ""

        print(f"✅ 实际路由: {actual_route}")
        print(f"⏱️  响应时间: {elapsed_time:.2f}s")
        print(f"📝 回复长度: {len(response)} 字符")
        print(f"🧠 路由逻辑: {logic}")
        print(f"\n💬 回复内容:")
        print("-" * 80)
        print(response)
        print("-" * 80)

        # 验证是否使用了LightRAG
        used_lightrag = False
        lightrag_indicators = [
            "LightRAG",
            "lightrag",
            "根据现有资料",
            "根据提供的知识库",
            "根据提供的资料",
            "从知识库检索"
        ]

        for indicator in lightrag_indicators:
            if indicator.lower() in response.lower() or indicator in logic.lower():
                used_lightrag = True
                break

        # 验证是否包含预期的关键词
        keyword_matches = []
        for keyword in test_case['expected_keywords']:
            if keyword in response:
                keyword_matches.append(keyword)

        # 检查回复是否来自LightRAG（LightRAG通常有特定的回复格式）
        is_lightrag_format = "根据" in response and ("资料" in response or "知识库" in response)

        print(f"\n🔍 验证结果:")
        print(f"   路由正确: {'✅' if actual_route == test_case['expected_route'] else '❌'}")
        print(f"   使用LightRAG: {'✅' if used_lightrag or is_lightrag_format else '❌'}")
        print(f"   LightRAG格式: {'✅' if is_lightrag_format else '❌'}")
        print(f"   关键词匹配: {len(keyword_matches)}/{len(test_case['expected_keywords'])} ({', '.join(keyword_matches[:3])}{'...' if len(keyword_matches) > 3 else ''})")

        # 评估回复质量
        quality_score = 0
        if len(response) > 100: quality_score += 1  # 内容详细
        if any(keyword in response for keyword in test_case['expected_keywords']): quality_score += 1  # 相关性
        if is_lightrag_format: quality_score += 1  # 格式正确

        print(f"   质量评分: {quality_score}/3")

        return {
            "question": test_case['question'],
            "description": test_case['description'],
            "expected_route": test_case['expected_route'],
            "actual_route": actual_route,
            "route_match": actual_route == test_case['expected_route'],
            "used_lightrag": used_lightrag or is_lightrag_format,
            "is_lightrag_format": is_lightrag_format,
            "keyword_matches": keyword_matches,
            "keyword_match_rate": len(keyword_matches) / len(test_case['expected_keywords']),
            "quality_score": quality_score,
            "response_time": elapsed_time,
            "response": response,
            "logic": logic
        }

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "question": test_case['question'],
            "description": test_case['description'],
            "error": str(e),
            "used_lightrag": False,
            "quality_score": 0
        }

async def main():
    """主测试函数"""
    print("🔍 测试LightRAG图查询功能")
    print("=" * 80)
    print("注意：这里测试的是kb-query路由是否会使用LightRAG的历史数据")
    print("=" * 80)

    results = []

    for test_case in LIGHTRAG_GRAPH_TESTS:
        result = await test_lightrag_graph_query(test_case)
        results.append(result)
        print("\n" + "=" * 80)

    # 汇总统计
    print("\n📊 LightRAG图查询测试汇总")
    print("=" * 80)

    total_tests = len(results)
    route_passed = sum(1 for r in results if r.get("route_match", False))
    lightrag_used = sum(1 for r in results if r.get("used_lightrag", False))
    avg_quality = sum(r.get("quality_score", 0) for r in results) / total_tests if total_tests > 0 else 0
    avg_keyword_rate = sum(r.get("keyword_match_rate", 0) for r in results) / total_tests if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"路由正确: {route_passed}/{total_tests}")
    print(f"使用LightRAG: {lightrag_used}/{total_tests}")
    print(f"平均质量评分: {avg_quality:.1f}/3")
    print(f"平均关键词匹配率: {avg_keyword_rate:.1%}")

    # 详细结果
    print(f"\n📋 详细测试结果:")
    for i, result in enumerate(results, 1):
        if "error" not in result:
            print(f"  {i}. {result['description']}")
            print(f"     路由: {result['actual_route']} {'✅' if result['route_match'] else '❌'}")
            print(f"     LightRAG: {'✅' if result['used_lightrag'] else '❌'}")
            print(f"     质量评分: {result['quality_score']}/3")
            print(f"     关键词匹配: {result['keyword_match_rate']:.1%}")

    # 判断LightRAG是否正常工作
    print(f"\n🎯 LightRAG工作状态评估:")
    if lightrag_used == total_tests and avg_quality >= 2:
        print("   ✅ LightRAG图查询功能正常工作")
    elif lightrag_used > 0:
        print("   ⚠️  LightRAG部分工作，可能需要优化")
    else:
        print("   ❌ LightRAG图查询功能未正常工作")

    print("\n🎉 测试完成!")
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
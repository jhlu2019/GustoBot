#!/usr/bin/env python3
"""
测试graphrag-query路由是否通过custom-tools调用LightRAG
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

logger = get_logger(service="test_graphrag_lightrag")

# 专门测试graphrag-query调用LightRAG的测试用例
GRAPHRAG_LIGHTRAG_TESTS = [
    {
        "question": "川菜的历史背景是什么？",
        "expected_route": "graphrag-query",
        "description": "测试graphrag-query查询历史背景（应该使用LightRAG）",
        "should_use_lightrag": True,
        "expected_keywords": ["川菜", "历史", "背景", "特点"]
    },
    {
        "question": "宫保鸡丁的典故和历史",
        "expected_route": "graphrag-query",
        "description": "测试graphrag-query查询历史典故（应该使用LightRAG）",
        "should_use_lightrag": True,
        "expected_keywords": ["宫保鸡丁", "历史", "典故", "由来"]
    },
    {
        "question": "中国菜系的发展历程",
        "expected_route": "graphrag-query",
        "description": "测试graphrag-query查询菜系发展（应该使用LightRAG）",
        "should_use_lightrag": True,
        "expected_keywords": ["菜系", "发展", "历史", "中国"]
    },
    {
        "question": "火锅的起源和文化意义",
        "expected_route": "graphrag-query",
        "description": "测试graphrag-query查询文化意义（应该使用LightRAG）",
        "should_use_lightrag": True,
        "expected_keywords": ["火锅", "起源", "文化", "意义"]
    }
]

async def test_graphrag_lightrag_workflow(test_case: dict):
    """测试graphrag-query是否会调用LightRAG"""
    try:
        print(f"\n🧪 {test_case['description']}")
        print(f"❓ 问题: {test_case['question']}")
        print(f"🎯 预期路由: {test_case['expected_route']} (graphrag-query)")
        print(f"🔍 应该通过custom-tools调用LightRAG: {test_case['should_use_lightrag']}")

        # 创建AgentState
        state = AgentState(
            messages=[HumanMessage(content=test_case['question'])]
        )

        # 执行路由
        config = {"configurable": {"thread_id": f"graphrag_lightrag_test_{test_case['question'][:10]}"}}
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

        # 检查工作流信息
        steps = result.get("steps", [])
        if steps:
            print(f"🔄 执行步骤: {' → '.join(steps)}")

        print(f"\n💬 回复内容:")
        print("-" * 80)
        print(response[:800] + ("..." if len(response) > 800 else ""))
        print("-" * 80)

        # 验证路由
        route_correct = actual_route == test_case['expected_route']

        # 验证是否使用了LightRAG特征
        lightrag_indicators = [
            "根据现有资料",
            "根据提供的资料",
            "从知识库检索",
            "### References",
            "按汤底风味分类",
            "源自中国",
            "以共享一锅热汤为基础"
        ]

        used_lightrag = any(indicator in response for indicator in lightrag_indicators)

        # 验证是否包含预期关键词
        keyword_matches = []
        for keyword in test_case['expected_keywords']:
            if keyword in response:
                keyword_matches.append(keyword)

        # 检查是否是Neo4j数据（结构化菜谱数据）
        neo4j_indicators = [
            "### 数据统计",
            "SQL命令分析",
            "查询结果摘要",
            "涉及表",
            "关键字段"
        ]

        is_neo4j_data = any(indicator in response for indicator in neo4j_indicators)

        # 判断数据来源
        if used_lightrag:
            data_source = "LightRAG"
        elif is_neo4j_data:
            data_source = "Neo4j"
        elif len(response) > 100:
            data_source = "其他知识源"
        else:
            data_source = "无数据"

        print(f"\n🔍 验证结果:")
        print(f"   路由正确: {'✅' if route_correct else '❌'} ({actual_route})")
        print(f"   数据来源: {data_source}")
        print(f"   使用LightRAG: {'✅' if used_lightrag else '❌'}")
        print(f"   使用Neo4j: {'✅' if is_neo4j_data else '❌'}")
        print(f"   关键词匹配: {len(keyword_matches)}/{len(test_case['expected_keywords'])} ({', '.join(keyword_matches[:3]) if keyword_matches else '无'}{'...' if len(keyword_matches) > 3 else ''})")

        # 评估回复质量
        quality_score = 0
        if len(response) > 200: quality_score += 1  # 内容详细
        if any(keyword in response for keyword in test_case['expected_keywords']): quality_score += 1  # 相关性
        if used_lightrag or is_neo4j_data: quality_score += 1  # 有数据来源

        print(f"   质量评分: {quality_score}/3")

        # 特别检查：如果问题是历史类但走了Neo4j，说明路由需要优化
        if any(word in test_case['question'] for word in ["历史", "典故", "背景", "起源"]) and is_neo4j_data:
            print(f"   ⚠️  注意: 历史类问题使用了Neo4j而不是LightRAG")

        return {
            "question": test_case['question'],
            "description": test_case['description'],
            "expected_route": test_case['expected_route'],
            "actual_route": actual_route,
            "route_match": route_correct,
            "data_source": data_source,
            "used_lightrag": used_lightrag,
            "used_neo4j": is_neo4j_data,
            "keyword_matches": keyword_matches,
            "keyword_match_rate": len(keyword_matches) / len(test_case['expected_keywords']),
            "quality_score": quality_score,
            "response_time": elapsed_time,
            "response": response,
            "logic": logic,
            "steps": steps
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
            "used_neo4j": False,
            "quality_score": 0
        }

async def main():
    """主测试函数"""
    print("🔍 测试graphrag-query路由是否调用LightRAG")
    print("=" * 80)
    print("设计预期: graphrag-query → custom-tools → LightRAG")
    print("=" * 80)

    results = []

    for test_case in GRAPHRAG_LIGHTRAG_TESTS:
        result = await test_graphrag_lightrag_workflow(test_case)
        results.append(result)
        print("\n" + "=" * 80)

    # 汇总统计
    print("\n📊 graphrag-query + LightRAG 测试汇总")
    print("=" * 80)

    total_tests = len(results)
    route_passed = sum(1 for r in results if r.get("route_match", False))
    lightrag_used = sum(1 for r in results if r.get("used_lightrag", False))
    neo4j_used = sum(1 for r in results if r.get("used_neo4j", False))
    avg_quality = sum(r.get("quality_score", 0) for r in results) / total_tests if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"路由正确: {route_passed}/{total_tests}")
    print(f"使用LightRAG: {lightrag_used}/{total_tests}")
    print(f"使用Neo4j: {neo4j_used}/{total_tests}")
    print(f"平均质量评分: {avg_quality:.1f}/3")

    # 详细结果
    print(f"\n📋 详细测试结果:")
    for i, result in enumerate(results, 1):
        if "error" not in result:
            print(f"  {i}. {result['description']}")
            print(f"     路由: {result['actual_route']} {'✅' if result['route_match'] else '❌'}")
            print(f"     数据源: {result['data_source']}")
            print(f"     质量评分: {result['quality_score']}/3")
            if result.get('steps'):
                print(f"     执行步骤: {' → '.join(result['steps'])}")

    # 判断graphrag-query到LightRAG的集成状态
    print(f"\n🎯 graphrag-query → LightRAG 集成状态:")
    if lightrag_used > 0:
        print(f"   ✅ {lightrag_used}/{total_tests} 个查询成功使用LightRAG")
    else:
        print("   ❌ graphrag-query没有调用LightRAG")
        print("   可能需要:")
        print("   1. 在custom-tools中添加LightRAG工具")
        print("   2. 修改graphrag-query工作流以包含LightRAG选项")
        print("   3. 优化路由逻辑以区分历史类和操作类查询")

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
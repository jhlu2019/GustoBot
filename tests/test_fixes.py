"""
测试修复效果 - 只测试之前失败的3个用例
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from langchain_core.messages import HumanMessage

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gustobot.application.agents.lg_builder import graph
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="test_fixes")

# 测试之前失败的用例
TEST_CASES = [
    {
        "question": "我想做菜",
        "expected_route": "additional-query",
        "description": "修复1: Additional-Query Guardrails空值问题",
        "issue": "之前返回 'NoneType' has no attribute 'decision'"
    },
    {
        "question": "怎么判断鱼熟了",
        "expected_route": "graphrag-query",
        "description": "修复2: GraphRAG Cypher验证格式错误",
        "issue": "之前出现 Pydantic validation error"
    },
    {
        "question": "哪个菜系的菜谱最多",
        "expected_route": "text2sql-query",
        "description": "修复3: Text2SQL安全检查（应能正常执行）",
        "issue": "之前被误拦截为非只读查询"
    },
]

async def test_single_case(test_case, session_id):
    """测试单个用例"""
    print(f"\n{'='*80}")
    print(f"测试: {test_case['description']}")
    print(f"问题: {test_case['question']}")
    print(f"之前的问题: {test_case['issue']}")
    print(f"{'='*80}")

    config = {"configurable": {"thread_id": session_id}}
    input_state = {"messages": [HumanMessage(content=test_case['question'])]}

    try:
        start_time = datetime.now()
        result = await graph.ainvoke(input_state, config=config)
        elapsed = (datetime.now() - start_time).total_seconds()

        actual_route = result.get('router', {}).get('type', 'unknown')
        response = result['messages'][-1].content if result.get('messages') else ''

        route_match = actual_route == test_case['expected_route']
        status = "✅ PASS" if route_match else "⚠️ ROUTE MISMATCH"

        print(f"实际路由: {actual_route}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复: {response[:200]}...")
        print(f"状态: {status}")

        return {
            "test_case": test_case['description'],
            "route_match": route_match,
            "actual_route": actual_route,
            "response_time": elapsed,
            "status": status,
            "error": None
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "test_case": test_case['description'],
            "route_match": False,
            "error": str(e),
            "status": "❌ ERROR"
        }

async def run_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("修复验证测试 - 测试之前失败的3个用例")
    print("="*80)

    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        result = await test_single_case(test_case, session_id=f"fix_test_{i}")
        results.append(result)
        if i < len(TEST_CASES):
            await asyncio.sleep(2)

    # 统计
    total = len(results)
    no_error = sum(1 for r in results if r.get("error") is None)
    passed = sum(1 for r in results if r.get("route_match", False))

    print("\n" + "="*80)
    print("测试汇总")
    print("="*80)
    print(f"总计: {total}")
    print(f"无错误: {no_error}/{total} ({'✅' if no_error == total else '⚠️'})")
    print(f"路由匹配: {passed}/{total}")

    if no_error == total:
        print("\n🎉 所有测试都没有抛出错误，修复成功！")
    else:
        print("\n⚠️ 仍有测试出现错误:")
        for r in results:
            if r.get("error"):
                print(f"  - {r['test_case']}: {r['error']}")

    print("="*80)
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(run_tests())
        # 如果所有测试都没有错误，退出码为0
        sys.exit(0 if all(r.get("error") is None for r in results) else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
测试 PostgreSQL pgvector 优先 + Milvus 兜底逻辑
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from langchain_core.messages import HumanMessage

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gustobot.application.agents.lg_builder import graph
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="test_pgvector_priority")


# 测试用例：验证 pgvector 优先逻辑
TEST_QUESTIONS = [
    {
        "question": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query",
        "description": "历史典故查询 - 应该路由到 kb-query",
        "check_tools": True,  # 检查是否包含 postgres
    },
    {
        "question": "川菜的特点和历史背景",
        "expected_route": "kb-query",
        "description": "菜系特点查询 - 应该路由到 kb-query",
        "check_tools": True,
    },
    {
        "question": "红烧肉这道菜的文化背景",
        "expected_route": "kb-query",
        "description": "文化背景查询 - 应该路由到 kb-query",
        "check_tools": True,
    },
]


async def test_single_question(question_data: dict, session_id: str):
    """测试单个问题"""

    question = question_data["question"]
    expected_route = question_data["expected_route"]
    description = question_data["description"]
    check_tools = question_data.get("check_tools", False)

    print(f"\n{'='*100}")
    print(f"[{description}]")
    print(f"问题: {question}")
    print(f"预期路由: {expected_route}")
    print(f"{'='*100}")

    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }

    input_state = {
        "messages": [HumanMessage(content=question)]
    }

    try:
        start_time = datetime.now()
        result = await graph.ainvoke(input_state, config=config)
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        actual_route = result.get('router', {}).get('type', 'unknown')
        logic = result.get('router', {}).get('logic', '')
        response = result['messages'][-1].content if result.get('messages') else ''

        # 检查工具选择（如果是 kb-query）
        tools_info = ""
        if check_tools and actual_route == "kb-query":
            # 尝试从结果中提取工具信息
            # 注意：这需要根据实际的 state 结构调整
            kb_tools = result.get('kb_tools', [])
            tools_info = f"\n工具选择: {kb_tools}"

            # 检查是否包含 postgres
            if 'postgres' in kb_tools:
                print(f"✅ 工具列表包含 postgres: {kb_tools}")
            else:
                print(f"⚠️ 工具列表未包含 postgres: {kb_tools}")

        route_match = actual_route == expected_route
        status = "✅ PASS" if route_match else "❌ FAIL"

        print(f"实际路由: {actual_route}")
        print(f"路由逻辑: {logic}")
        print(f"{tools_info}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复前150字: {response[:150]}...")
        print(f"状态: {status}")

        return {
            "question": question,
            "expected": expected_route,
            "actual": actual_route,
            "match": route_match,
            "logic": logic,
            "tools": result.get('kb_tools', []),
            "time": elapsed,
        }

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "question": question,
            "expected": expected_route,
            "actual": "ERROR",
            "match": False,
            "error": error_msg,
        }


async def run_tests():
    """运行所有测试"""

    print("\n" + "="*100)
    print("测试 PostgreSQL pgvector 优先 + Milvus 兜底逻辑")
    print("="*100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    for i, question_data in enumerate(TEST_QUESTIONS, 1):
        session_id = f"test_pgvector_{timestamp}_{i}"
        result = await test_single_question(question_data, session_id)
        results.append(result)

        # 避免请求过快
        if i < len(TEST_QUESTIONS):
            await asyncio.sleep(2)

    # 统计汇总
    total = len(results)
    passed = sum(1 for r in results if r.get("match", False))
    failed = total - passed

    # 检查工具选择
    postgres_count = sum(1 for r in results if 'postgres' in r.get("tools", []))
    milvus_count = sum(1 for r in results if 'milvus' in r.get("tools", []))

    print("\n" + "="*100)
    print("测试汇总")
    print("="*100)
    print(f"总计: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"成功率: {passed/total*100:.1f}%")
    print(f"\n工具选择统计:")
    print(f"包含 postgres: {postgres_count}/{total} ({postgres_count/total*100:.1f}%)")
    print(f"包含 milvus: {milvus_count}/{total} ({milvus_count/total*100:.1f}%)")

    if postgres_count == total:
        print(f"\n✅ 所有 kb-query 都正确包含了 postgres 工具！")
    else:
        print(f"\n⚠️ 有 {total - postgres_count} 个查询未包含 postgres")

    print("="*100)
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_tests())

        # 检查是否所有 kb-query 都包含 postgres
        kb_results = [r for r in results if r['actual'] == 'kb-query']
        postgres_in_all = all('postgres' in r.get('tools', []) for r in kb_results)

        if postgres_in_all:
            print("\n🎉 PostgreSQL 优先策略已生效！")
        else:
            print("\n⚠️ PostgreSQL 优先策略未完全生效，需要进一步检查")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

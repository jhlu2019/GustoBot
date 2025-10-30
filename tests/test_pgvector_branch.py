"""
测试 kb-query 路由中的 pgvector (postgres) 分支是否能正常工作

测试重点：
1. 路由器是否能正确选择 postgres 工具
2. postgres 检索服务是否可访问
3. 检索结果是否正确返回
4. 最终答案是否包含 postgres 来源信息
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

logger = get_logger(service="test_pgvector")

# 测试用例：针对 postgres 结构化查询的问题
TEST_CASES = [
    {
        "question": "数据库里有多少道川菜",
        "expected_route": "kb-query",
        "expected_tools": ["postgres"],
        "description": "统计查询（应触发 postgres）",
        "rationale": "涉及结构化数据统计，postgres 更适合"
    },
    {
        "question": "哪些菜谱的烹饪时间最短",
        "expected_route": "kb-query",
        "expected_tools": ["postgres"],
        "description": "排序查询（应触发 postgres）",
        "rationale": "涉及字段排序，结构化查询更高效"
    },
    {
        "question": "有哪些难度为简单的菜谱",
        "expected_route": "kb-query",
        "expected_tools": ["postgres"],
        "description": "过滤查询（应触发 postgres）",
        "rationale": "枚举字段过滤，结构化数据库更合适"
    },
    {
        "question": "红烧肉的文化背景是什么",
        "expected_route": "kb-query",
        "expected_tools": ["milvus"],
        "description": "语义查询（应触发 milvus）",
        "rationale": "文化背景属于非结构化内容，向量检索更合适"
    },
    {
        "question": "川菜有哪些特色菜谱",
        "expected_route": "kb-query",
        "expected_tools": ["milvus", "postgres"],
        "description": "混合查询（可能触发双工具）",
        "rationale": "既涉及菜系过滤（结构化）又涉及特色描述（语义）"
    },
]


async def test_pgvector_case(test_case, session_id):
    """测试单个 pgvector 用例"""
    print(f"\n{'='*80}")
    print(f"测试: {test_case['description']}")
    print(f"问题: {test_case['question']}")
    print(f"预期路由: {test_case['expected_route']}")
    print(f"预期工具: {test_case['expected_tools']}")
    print(f"理由: {test_case['rationale']}")
    print(f"{'='*80}")

    config = {"configurable": {"thread_id": session_id}}
    input_state = {"messages": [HumanMessage(content=test_case['question'])]}

    try:
        start_time = datetime.now()
        result = await graph.ainvoke(input_state, config=config)
        elapsed = (datetime.now() - start_time).total_seconds()

        # 提取关键信息
        actual_route = result.get('router', {}).get('type', 'unknown')
        router_logic = result.get('router', {}).get('logic', '')
        response = result['messages'][-1].content if result.get('messages') else ''

        # 尝试从结果中提取 KB 工具信息
        kb_tools = result.get('kb_tools', [])
        kb_route = result.get('kb_route', 'unknown')
        milvus_results = result.get('milvus_results', [])
        postgres_results = result.get('postgres_results', [])

        # 判断是否成功
        route_match = actual_route == test_case['expected_route']

        # 检查工具使用（如果路由正确）
        tools_used = []
        if len(milvus_results) > 0:
            tools_used.append("milvus")
        if len(postgres_results) > 0:
            tools_used.append("postgres")

        tools_match = any(tool in tools_used for tool in test_case['expected_tools'])

        # 综合判断
        if route_match and (tools_match or not tools_used):
            status = "✅ PASS"
        elif route_match:
            status = "⚠️ PARTIAL (路由对但工具不符)"
        else:
            status = "❌ FAIL"

        # 输出结果
        print(f"\n实际路由: {actual_route} {'✅' if route_match else '❌'}")
        print(f"路由逻辑: {router_logic}")
        print(f"KB路由决策: {kb_route}")
        print(f"选中的工具: {kb_tools}")
        print(f"实际使用的工具: {tools_used}")
        print(f"Milvus结果数: {len(milvus_results)}")
        print(f"Postgres结果数: {len(postgres_results)}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复摘要: {response[:200]}...")
        print(f"\n最终状态: {status}")

        # 检查 postgres 分支是否畅通
        postgres_working = False
        postgres_error = None

        if "postgres" in test_case['expected_tools']:
            if len(postgres_results) > 0:
                postgres_working = True
                print(f"\n✅ Postgres 分支工作正常！返回了 {len(postgres_results)} 条结果")
                print(f"示例结果: {json.dumps(postgres_results[0], ensure_ascii=False, indent=2)[:300]}...")
            elif "postgres" in tools_used:
                postgres_error = "Postgres工具被选中但未返回结果"
                print(f"\n⚠️ {postgres_error}")
            else:
                postgres_error = "Postgres工具未被路由器选中"
                print(f"\n⚠️ {postgres_error}")

        return {
            "test_case": test_case['description'],
            "question": test_case['question'],
            "route_match": route_match,
            "tools_match": tools_match,
            "actual_route": actual_route,
            "kb_route": kb_route,
            "selected_tools": kb_tools,
            "used_tools": tools_used,
            "milvus_count": len(milvus_results),
            "postgres_count": len(postgres_results),
            "postgres_working": postgres_working,
            "postgres_error": postgres_error,
            "response_time": elapsed,
            "status": status,
            "response_snippet": response[:500],
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "test_case": test_case['description'],
            "question": test_case['question'],
            "route_match": False,
            "tools_match": False,
            "error": str(e),
            "status": "❌ ERROR"
        }


async def run_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("GustoBot KB-Query Pgvector 分支测试")
    print("="*80)

    results = []
    for i, test_case in enumerate(TEST_CASES, 1):
        result = await test_pgvector_case(test_case, session_id=f"pgvector_test_{i}")
        results.append(result)

        if i < len(TEST_CASES):
            await asyncio.sleep(2)

    # 统计
    total = len(results)
    passed = sum(1 for r in results if r['status'].startswith('✅'))
    partial = sum(1 for r in results if r['status'].startswith('⚠️'))
    failed = sum(1 for r in results if r['status'].startswith('❌'))

    postgres_tests = [r for r in results if 'postgres_working' in r]
    postgres_working = sum(1 for r in postgres_tests if r.get('postgres_working', False))

    print("\n" + "="*80)
    print("测试汇总")
    print("="*80)
    print(f"总计: {total}")
    print(f"✅ 完全通过: {passed}")
    print(f"⚠️ 部分通过: {partial}")
    print(f"❌ 失败: {failed}")
    print(f"\n📊 Postgres 分支测试:")
    print(f"  期望使用 postgres: {len(postgres_tests)}")
    print(f"  实际工作正常: {postgres_working}/{len(postgres_tests)}")

    if postgres_working > 0:
        print(f"\n🎉 Postgres 分支至少有 {postgres_working} 个用例工作正常！")
    else:
        print(f"\n⚠️ 警告：所有 Postgres 测试都未成功！")
        print("可能原因：")
        print("  1. INGEST_SERVICE_URL 配置错误")
        print("  2. kb_ingest 服务未运行")
        print("  3. PostgreSQL 数据库为空")
        print("  4. 路由器未选择 postgres 工具")

    # 详细错误信息
    postgres_errors = [r for r in postgres_tests if r.get('postgres_error')]
    if postgres_errors:
        print(f"\n⚠️ Postgres 相关错误:")
        for r in postgres_errors:
            print(f"  - {r['test_case']}: {r['postgres_error']}")

    print("="*80)

    # 保存结果
    output_file = Path(__file__).parent / "test_pgvector_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到: {output_file}")

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_tests())

        # 检查是否有 postgres 工作
        postgres_working = any(
            r.get('postgres_working', False)
            for r in results
            if 'postgres_working' in r
        )

        if postgres_working:
            print("\n✅ 测试完成！Postgres 分支工作正常。")
            sys.exit(0)
        else:
            print("\n⚠️ 测试完成，但 Postgres 分支未能成功工作。")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

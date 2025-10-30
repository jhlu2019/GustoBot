"""
快速路由测试脚本 - 测试关键场景并保存详细结果
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from langchain_core.messages import HumanMessage

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gustobot.application.agents.lg_builder import graph
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="test_quick_routing")


# 精选测试用例（每种路由类型1-2个代表性问题）
TEST_QUESTIONS = [
    # 1. General-Query
    {"question": "你好", "expected_route": "general-query", "description": "基本问候"},

    # 2. Additional-Query
    {"question": "我想做菜", "expected_route": "additional-query", "description": "模糊提问"},
    {"question": "今天天气怎么样", "expected_route": "additional-query", "description": "无关问题（Guardrails拦截）"},

    # 3. KB-Query
    {"question": "宫保鸡丁的历史典故是什么", "expected_route": "kb-query", "description": "历史典故查询"},
    {"question": "川菜的特点是什么", "expected_route": "kb-query", "description": "地域流派介绍"},

    # 4. GraphRAG-Query
    {"question": "红烧肉怎么做", "expected_route": "graphrag-query", "description": "菜谱做法（Cypher）"},
    {"question": "宫保鸡丁需要哪些食材", "expected_route": "graphrag-query", "description": "食材查询（Cypher）"},
    {"question": "怎么判断鱼熟了", "expected_route": "graphrag-query", "description": "技巧推理（GraphRAG）"},

    # 5. Text2SQL-Query
    {"question": "数据库里有多少道菜", "expected_route": "text2sql-query", "description": "统计查询"},
    {"question": "哪个菜系的菜谱最多", "expected_route": "text2sql-query", "description": "排名查询"},
]


async def test_single_question(question_data: dict, session_id: str, result_file):
    """测试单个问题并保存详细结果"""

    question = question_data["question"]
    expected_route = question_data["expected_route"]
    description = question_data["description"]

    print(f"\n{'='*80}")
    print(f"测试: {description}")
    print(f"问题: {question}")
    print(f"预期路由: {expected_route}")
    print(f"{'='*80}")

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

        route_match = actual_route == expected_route
        status = "✅ PASS" if route_match else "❌ FAIL"

        # 输出到控制台
        print(f"实际路由: {actual_route}")
        print(f"路由逻辑: {logic}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复摘要: {response[:200]}...")
        print(f"状态: {status}")

        # 保存详细结果
        result_data = {
            "timestamp": start_time.isoformat(),
            "test_case": description,
            "question": question,
            "expected_route": expected_route,
            "actual_route": actual_route,
            "route_match": route_match,
            "logic": logic,
            "response_time_seconds": elapsed,
            "full_response": response,
            "status": status,
        }

        # 追加到结果文件
        result_file.write(json.dumps(result_data, ensure_ascii=False, indent=2))
        result_file.write(",\n")

        return result_data

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")

        error_data = {
            "timestamp": datetime.now().isoformat(),
            "test_case": description,
            "question": question,
            "expected_route": expected_route,
            "actual_route": "ERROR",
            "route_match": False,
            "error": error_msg,
            "status": "❌ ERROR",
        }

        result_file.write(json.dumps(error_data, ensure_ascii=False, indent=2))
        result_file.write(",\n")

        return error_data


async def run_tests():
    """运行所有测试"""

    print("\n" + "="*80)
    print("GustoBot Agent 路由快速测试")
    print("="*80)

    # 创建结果文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file_path = Path(__file__).parent / f"test_results_{timestamp}.json"

    results = []

    with open(result_file_path, 'w', encoding='utf-8') as f:
        f.write("[\n")

        for i, question_data in enumerate(TEST_QUESTIONS, 1):
            session_id = f"test_{timestamp}_{i}"
            result = await test_single_question(question_data, session_id, f)
            results.append(result)

            # 避免请求过快
            if i < len(TEST_QUESTIONS):
                await asyncio.sleep(2)

        # 移除最后的逗号
        f.seek(f.tell() - 2)
        f.write("\n]\n")

    # 统计汇总
    total = len(results)
    passed = sum(1 for r in results if r.get("route_match", False))
    failed = total - passed
    errors = sum(1 for r in results if "error" in r)

    print("\n" + "="*80)
    print("测试汇总")
    print("="*80)
    print(f"总计: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"错误: {errors} ⚠️")
    print(f"成功率: {passed/total*100:.1f}%")
    print(f"结果已保存到: {result_file_path}")
    print("="*80)

    # 输出失败详情
    if failed > 0:
        print("\n失败的测试用例:")
        for r in results:
            if not r.get("route_match", False) and "error" not in r:
                print(f"  ❌ {r['test_case']}")
                print(f"     问题: {r['question']}")
                print(f"     预期: {r['expected_route']}")
                print(f"     实际: {r['actual_route']}")
                print(f"     逻辑: {r.get('logic', 'N/A')}")
                print()

    return results, result_file_path


if __name__ == "__main__":
    try:
        results, result_file = asyncio.run(run_tests())
        print(f"\n✅ 测试完成！结果已保存到: {result_file}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

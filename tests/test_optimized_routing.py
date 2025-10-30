"""
测试优化后的Text2SQL和KB-Query路由
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

logger = get_logger(service="test_optimized_routing")


# 针对性测试用例
TEST_QUESTIONS = [
    # ========== Text2SQL 路由测试 ==========
    {
        "question": "数据库里有多少道菜",
        "expected_route": "text2sql-query",
        "description": "统计查询 - 数量",
        "category": "text2sql"
    },
    {
        "question": "哪个菜系的菜谱最多",
        "expected_route": "text2sql-query",
        "description": "排名查询",
        "category": "text2sql"
    },
    {
        "question": "统计有多少道川菜",
        "expected_route": "text2sql-query",
        "description": "分类统计",
        "category": "text2sql"
    },
    {
        "question": "计算各菜系的菜谱数量",
        "expected_route": "text2sql-query",
        "description": "分组统计",
        "category": "text2sql"
    },
    {
        "question": "最受欢迎的5道菜是什么",
        "expected_route": "text2sql-query",
        "description": "TOP排名查询",
        "category": "text2sql"
    },

    # ========== KB-Query 路由测试（应该走向量库） ==========
    {
        "question": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query",
        "description": "历史典故查询（应选择milvus）",
        "category": "kb-query"
    },
    {
        "question": "川菜的特点和历史背景",
        "expected_route": "kb-query",
        "description": "菜系特点查询（应选择milvus）",
        "category": "kb-query"
    },
    {
        "question": "红烧肉这道菜的文化背景",
        "expected_route": "kb-query",
        "description": "文化背景查询（应选择milvus）",
        "category": "kb-query"
    },

    # ========== GraphRAG 路由测试（不应该走KB-Query） ==========
    {
        "question": "红烧肉怎么做",
        "expected_route": "graphrag-query",
        "description": "做法查询（不应该走kb-query）",
        "category": "graphrag"
    },
    {
        "question": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query",
        "description": "食材查询（不应该走kb-query）",
        "category": "graphrag"
    },
    {
        "question": "怎么判断鱼熟了",
        "expected_route": "graphrag-query",
        "description": "烹饪技巧（不应该走kb-query）",
        "category": "graphrag"
    },
]


async def test_single_question(question_data: dict, session_id: str):
    """测试单个问题"""

    question = question_data["question"]
    expected_route = question_data["expected_route"]
    description = question_data["description"]
    category = question_data["category"]

    print(f"\n{'='*100}")
    print(f"[{category}] {description}")
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

        route_match = actual_route == expected_route
        status = "✅ PASS" if route_match else "❌ FAIL"

        print(f"实际路由: {actual_route}")
        print(f"路由逻辑: {logic}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复前150字: {response[:150]}...")
        print(f"状态: {status}")

        return {
            "question": question,
            "category": category,
            "expected": expected_route,
            "actual": actual_route,
            "match": route_match,
            "logic": logic,
            "time": elapsed,
        }

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")
        return {
            "question": question,
            "category": category,
            "expected": expected_route,
            "actual": "ERROR",
            "match": False,
            "error": error_msg,
        }


async def run_tests():
    """运行所有测试"""

    print("\n" + "="*100)
    print("测试优化后的路由 - Text2SQL & KB-Query")
    print("="*100)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    for i, question_data in enumerate(TEST_QUESTIONS, 1):
        session_id = f"test_opt_{timestamp}_{i}"
        result = await test_single_question(question_data, session_id)
        results.append(result)

        # 避免请求过快
        if i < len(TEST_QUESTIONS):
            await asyncio.sleep(2)

    # 统计汇总
    total = len(results)
    passed = sum(1 for r in results if r.get("match", False))
    failed = total - passed
    errors = sum(1 for r in results if "error" in r)

    # 按类别统计
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0}
        categories[cat]["total"] += 1
        if r.get("match", False):
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    print("\n" + "="*100)
    print("测试汇总")
    print("="*100)
    print(f"总计: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"错误: {errors} ⚠️")
    print(f"成功率: {passed/total*100:.1f}%")

    # 按类别显示统计
    print("\n" + "="*100)
    print("按类别统计")
    print("="*100)
    for cat, stats in sorted(categories.items()):
        success_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        status_icon = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
        print(f"{status_icon} {cat:15} - 总计:{stats['total']:2}  通过:{stats['passed']:2}  失败:{stats['failed']:2}  成功率:{success_rate:5.1f}%")

    # 输出失败详情
    if failed > 0:
        print("\n" + "="*100)
        print("失败的测试用例")
        print("="*100)
        for r in results:
            if not r.get("match", False) and "error" not in r:
                print(f"❌ [{r['category']}] {r['question']}")
                print(f"   预期: {r['expected']}")
                print(f"   实际: {r['actual']}")
                print(f"   逻辑: {r.get('logic', 'N/A')}")
                print()

    print("="*100)
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_tests())

        # 重点关注text2sql的结果
        text2sql_results = [r for r in results if r['category'] == 'text2sql']
        text2sql_pass = sum(1 for r in text2sql_results if r['match'])

        print(f"\n🎯 Text2SQL路由测试结果: {text2sql_pass}/{len(text2sql_results)} 通过")

        if text2sql_pass == len(text2sql_results):
            print("✅ Text2SQL路由已完全修复！")
        else:
            print("⚠️ Text2SQL路由仍有问题，需要进一步检查")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

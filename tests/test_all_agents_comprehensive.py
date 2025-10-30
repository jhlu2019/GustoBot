"""
全面测试所有Agent路由 - 包括所有路由类型的详细测试
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

logger = get_logger(service="test_all_agents")


# 全面的测试用例 - 覆盖所有路由类型
TEST_QUESTIONS = [
    # ========== 1. General-Query 路由测试 ==========
    {
        "question": "你好",
        "expected_route": "general-query",
        "description": "问候语测试",
        "category": "general-query"
    },
    {
        "question": "早上好",
        "expected_route": "general-query",
        "description": "问候语测试2",
        "category": "general-query"
    },
    {
        "question": "谢谢你",
        "expected_route": "general-query",
        "description": "礼貌用语测试",
        "category": "general-query"
    },
    {
        "question": "今天是个好天气",
        "expected_route": "general-query",
        "description": "闲聊测试",
        "category": "general-query"
    },

    # ========== 2. Additional-Query 路由测试 ==========
    {
        "question": "我想做菜",
        "expected_route": "additional-query",
        "description": "模糊提问需要补充信息",
        "category": "additional-query"
    },
    {
        "question": "怎么做好吃的",
        "expected_route": "additional-query",
        "description": "缺少具体菜名",
        "category": "additional-query"
    },
    {
        "question": "今天天气怎么样",
        "expected_route": "additional-query",
        "description": "无关问题（应触发guardrails拦截）",
        "category": "additional-query"
    },
    {
        "question": "最近有什么新闻",
        "expected_route": "additional-query",
        "description": "无关问题（应触发guardrails拦截）",
        "category": "additional-query"
    },

    # ========== 3. KB-Query 路由测试 (向量检索) ==========
    {
        "question": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query",
        "description": "菜谱历史典故查询（应该走向量检索）",
        "category": "kb-query"
    },
    {
        "question": "川菜的特点和历史背景",
        "expected_route": "kb-query",
        "description": "地域流派介绍（应该走向量检索）",
        "category": "kb-query"
    },
    {
        "question": "红烧肉这道菜的文化背景",
        "expected_route": "kb-query",
        "description": "菜品文化背景查询",
        "category": "kb-query"
    },

    # ========== 4. GraphRAG-Query 路由测试 (图查询) ==========
    # 4.1 固定Cypher查询（predefined_cypher）
    {
        "question": "红烧肉怎么做",
        "expected_route": "graphrag-query",
        "description": "菜谱做法查询（应走固定Cypher）",
        "category": "graphrag-cypher"
    },
    {
        "question": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query",
        "description": "食材查询（应走固定Cypher）",
        "category": "graphrag-cypher"
    },
    {
        "question": "麻婆豆腐的烹饪步骤",
        "expected_route": "graphrag-query",
        "description": "烹饪步骤查询（应走固定Cypher）",
        "category": "graphrag-cypher"
    },
    {
        "question": "糖醋排骨用什么烹饪方法",
        "expected_route": "graphrag-query",
        "description": "烹饪方法查询（应走固定Cypher）",
        "category": "graphrag-cypher"
    },

    # 4.2 LightRAG查询（更复杂的推理）
    {
        "question": "怎么判断鱼熟了",
        "expected_route": "graphrag-query",
        "description": "烹饪技巧推理（可能走LightRAG）",
        "category": "graphrag-lightrag"
    },
    {
        "question": "如何掌握炒菜的火候",
        "expected_route": "graphrag-query",
        "description": "烹饪技巧推理2（可能走LightRAG）",
        "category": "graphrag-lightrag"
    },
    {
        "question": "什么菜适合用蒸的方法做",
        "expected_route": "graphrag-query",
        "description": "菜谱推荐（可能走LightRAG）",
        "category": "graphrag-lightrag"
    },

    # ========== 5. Text2SQL-Query 路由测试 ==========
    {
        "question": "数据库里有多少道菜",
        "expected_route": "text2sql-query",
        "description": "统计查询",
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
]


async def test_single_question(question_data: dict, session_id: str, result_file):
    """测试单个问题并保存详细结果"""

    question = question_data["question"]
    expected_route = question_data["expected_route"]
    description = question_data["description"]
    category = question_data["category"]

    print(f"\n{'='*100}")
    print(f"类别: {category}")
    print(f"测试: {description}")
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

        # 输出到控制台
        print(f"实际路由: {actual_route}")
        print(f"路由逻辑: {logic}")
        print(f"响应时间: {elapsed:.2f}s")
        print(f"回复前200字: {response[:200]}...")
        print(f"状态: {status}")

        # 保存详细结果
        result_data = {
            "timestamp": start_time.isoformat(),
            "category": category,
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
        import traceback
        print(traceback.format_exc())

        error_data = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
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

    print("\n" + "="*100)
    print("GustoBot Agent 全面路由测试")
    print("="*100)

    # 创建结果文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file_path = Path(__file__).parent / f"test_results_comprehensive_{timestamp}.json"

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

    # 按类别统计
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0}
        categories[cat]["total"] += 1
        if r.get("route_match", False):
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
    print(f"\n结果已保存到: {result_file_path}")

    # 按类别显示统计
    print("\n" + "="*100)
    print("按类别统计")
    print("="*100)
    for cat, stats in sorted(categories.items()):
        success_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"{cat:20} - 总计:{stats['total']:2}  通过:{stats['passed']:2}  失败:{stats['failed']:2}  成功率:{success_rate:5.1f}%")

    # 输出失败详情
    if failed > 0:
        print("\n" + "="*100)
        print("失败的测试用例")
        print("="*100)
        for r in results:
            if not r.get("route_match", False) and "error" not in r:
                print(f"❌ [{r['category']}] {r['test_case']}")
                print(f"   问题: {r['question']}")
                print(f"   预期: {r['expected_route']}")
                print(f"   实际: {r['actual_route']}")
                print(f"   逻辑: {r.get('logic', 'N/A')}")
                print()

    # 输出错误详情
    if errors > 0:
        print("\n" + "="*100)
        print("错误的测试用例")
        print("="*100)
        for r in results:
            if "error" in r:
                print(f"⚠️  [{r['category']}] {r['test_case']}")
                print(f"   问题: {r['question']}")
                print(f"   错误: {r['error']}")
                print()

    print("="*100)
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

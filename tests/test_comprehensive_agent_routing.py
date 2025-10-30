"""
综合智能体路由测试脚本

测试 LangGraph 多 Agent 系统的路由功能，覆盖所有查询类型
执行方式：python test_comprehensive_agent_routing.py
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from langchain_core.messages import HumanMessage

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gustobot.application.agents.lg_builder import graph
from gustobot.application.agents.utils import new_uuid
from gustobot.infrastructure.core.logger import get_logger

logger = get_logger(service="test_comprehensive_agent_routing")


class RoutingTestCase:
    """路由测试用例"""

    def __init__(
        self,
        question: str,
        expected_route: str,
        expected_node: str,
        description: str,
        sub_decision: Optional[str] = None,
        image_path: Optional[str] = None,
        file_path: Optional[str] = None,
        category: str = "general"
    ):
        self.question = question
        self.expected_route = expected_route
        self.expected_node = expected_node
        self.description = description
        self.sub_decision = sub_decision
        self.image_path = image_path
        self.file_path = file_path
        self.category = category


class AgentTester:
    """Agent系统测试类"""

    def __init__(self):
        self.results = []
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "by_category": {},
            "response_times": []
        }

    async def test_query(self, test_case: RoutingTestCase, session_id: str = None) -> Dict[str, Any]:
        """测试单个查询"""
        if session_id is None:
            session_id = new_uuid()

        config = {
            "configurable": {
                "thread_id": session_id,
                "image_path": test_case.image_path,
                "file_path": test_case.file_path,
            }
        }

        input_state = {
            "messages": [HumanMessage(content=test_case.question)]
        }

        start_time = time.time()

        try:
            # 使用 astream 获取实时响应
            result = await graph.ainvoke(input_state, config=config)

            end_time = time.time()
            response_time = end_time - start_time

            actual_route = result.get('router', {}).get('type', 'unknown')
            actual_logic = result.get('router', {}).get('logic', '')
            response_text = result['messages'][-1].content if result.get('messages') else ''

            # 验证结果
            route_match = actual_route == test_case.expected_route

            # 更新统计信息
            self.stats["total"] += 1
            self.stats["response_times"].append(response_time)

            if test_case.category not in self.stats["by_category"]:
                self.stats["by_category"][test_case.category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            self.stats["by_category"][test_case.category]["total"] += 1

            if route_match:
                self.stats["passed"] += 1
                self.stats["by_category"][test_case.category]["passed"] += 1
                status = "✅ PASS"
            else:
                self.stats["failed"] += 1
                self.stats["by_category"][test_case.category]["failed"] += 1
                status = "❌ FAIL"

            # 构建结果
            test_result = {
                "timestamp": datetime.now().isoformat(),
                "test_case": test_case.description,
                "category": test_case.category,
                "question": test_case.question,
                "expected_route": test_case.expected_route,
                "actual_route": actual_route,
                "route_match": route_match,
                "logic": actual_logic,
                "response_time_seconds": round(response_time, 4),
                "full_response": response_text,
                "status": status,
                "expected_node": test_case.expected_node,
            }

            if test_case.sub_decision:
                test_result["expected_sub_decision"] = test_case.sub_decision

            self.results.append(test_result)

            # 打印结果
            self._print_test_result(test_result)

            return test_result

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            self.stats["total"] += 1
            self.stats["errors"] += 1
            self.stats["response_times"].append(response_time)

            if test_case.category not in self.stats["by_category"]:
                self.stats["by_category"][test_case.category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            self.stats["by_category"][test_case.category]["total"] += 1

            error_result = {
                "timestamp": datetime.now().isoformat(),
                "test_case": test_case.description,
                "category": test_case.category,
                "question": test_case.question,
                "expected_route": test_case.expected_route,
                "actual_route": "ERROR",
                "route_match": False,
                "error": str(e),
                "response_time_seconds": round(response_time, 4),
                "status": "❌ ERROR",
                "expected_node": test_case.expected_node,
            }

            self.results.append(error_result)

            # 打印错误
            self._print_test_result(error_result)

            return error_result

    def _print_test_result(self, result: Dict[str, Any]):
        """打印测试结果"""
        print(f"\n{'='*80}")
        print(f"测试: {result['test_case']}")
        print(f"类别: {result['category']}")
        print(f"问题: {result['question']}")
        print(f"预期路由: {result['expected_route']}")
        print(f"实际路由: {result['actual_route']}")
        print(f"路由逻辑: {result.get('logic', 'N/A')}")
        print(f"预期节点: {result.get('expected_node', 'N/A')}")
        if 'expected_sub_decision' in result:
            print(f"预期子决策: {result['expected_sub_decision']}")
        print(f"响应时间: {result['response_time_seconds']}秒")
        print(f"状态: {result['status']}")
        if 'full_response' in result:
            print(f"回复摘要: {result['full_response'][:200]}...")
        if 'error' in result:
            print(f"错误信息: {result['error']}")
        print(f"{'='*80}\n")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*100)
        print("测试总结报告")
        print("="*100)

        # 总体统计
        print(f"\n📊 总体统计:")
        print(f"  总测试数: {self.stats['total']}")
        print(f"  通过: {self.stats['passed']} ({self.stats['passed']/self.stats['total']*100:.1f}%)")
        print(f"  失败: {self.stats['failed']} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"  错误: {self.stats['errors']} ({self.stats['errors']/self.stats['total']*100:.1f}%)")

        # 响应时间统计
        if self.stats['response_times']:
            avg_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            min_time = min(self.stats['response_times'])
            max_time = max(self.stats['response_times'])
            print(f"\n⏱️ 响应时间统计:")
            print(f"  平均: {avg_time:.2f}秒")
            print(f"  最快: {min_time:.2f}秒")
            print(f"  最慢: {max_time:.2f}秒")

        # 分类统计
        print(f"\n📈 分类统计:")
        for category, stats in self.stats['by_category'].items():
            success_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {category}:")
            print(f"    总数: {stats['total']}")
            print(f"    通过: {stats['passed']} ({success_rate:.1f}%)")
            print(f"    失败: {stats['failed']}")

        print("\n" + "="*100)

    def save_results(self, filename: str = None):
        """保存测试结果到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_routing_test_results_{timestamp}.json"

        results_data = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "results": self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 测试结果已保存到: {filename}")


# ============================================================================
# 测试用例定义
# ============================================================================

TEST_CASES = [
    # ========== General-Query 测试 ==========
    RoutingTestCase(
        question="你好",
        expected_route="general-query",
        expected_node="respond_to_general_query",
        description="基本问候",
        category="general-query"
    ),
    RoutingTestCase(
        question="早上好",
        expected_route="general-query",
        expected_node="respond_to_general_query",
        description="礼貌寒暄",
        category="general-query"
    ),
    RoutingTestCase(
        question="谢谢你的帮助",
        expected_route="general-query",
        expected_node="respond_to_general_query",
        description="感谢反馈",
        category="general-query"
    ),
    RoutingTestCase(
        question="今天天气不错",
        expected_route="general-query",
        expected_node="respond_to_general_query",
        description="日常对话",
        category="general-query"
    ),
    RoutingTestCase(
        question="再见",
        expected_route="general-query",
        expected_node="respond_to_general_query",
        description="告别语",
        category="general-query"
    ),

    # ========== Additional-Query 测试 ==========
    RoutingTestCase(
        question="我想做菜",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="模糊提问（缺菜名）",
        category="additional-query"
    ),
    RoutingTestCase(
        question="这个菜怎么做好吃",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="缺少关键信息（哪道菜）",
        category="additional-query"
    ),
    RoutingTestCase(
        question="帮我推荐一道菜",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="需要更多信息才能推荐",
        category="additional-query"
    ),
    RoutingTestCase(
        question="今天天气怎么样",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="天气问题（需要补充地点）",
        category="additional-query"
    ),
    RoutingTestCase(
        question="有什么好吃的",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="过于笼统的问题",
        category="additional-query"
    ),

    # ========== KB-Query 测试（历史文化类） ==========
    RoutingTestCase(
        question="宫保鸡丁的历史典故是什么",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="菜谱历史典故",
        sub_decision="KB Multi-tool: Milvus 或 pgvector",
        category="kb-query"
    ),
    RoutingTestCase(
        question="佛跳墙这道菜的由来",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="菜品背景文化",
        sub_decision="KB Multi-tool: 智能选择向量检索源",
        category="kb-query"
    ),
    RoutingTestCase(
        question="川菜的特点是什么",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="地域流派介绍",
        sub_decision="KB Multi-tool: 可能合并多个来源",
        category="kb-query"
    ),
    RoutingTestCase(
        question="川菜大师有哪些",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="名厨偏好介绍",
        category="kb-query"
    ),
    RoutingTestCase(
        question="粤菜的发展历史",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="菜系历史发展",
        category="kb-query"
    ),
    RoutingTestCase(
        question="中国八大菜系的文化背景",
        expected_route="kb-query",
        expected_node="create_kb_query",
        description="菜系文化背景",
        category="kb-query"
    ),

    # ========== GraphRAG-Query 测试（做法步骤类） ==========
    RoutingTestCase(
        question="红烧肉怎么做",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问菜谱做法",
        sub_decision="cypher_query 或 predefined_cypher → Neo4j",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="宫保鸡丁需要哪些食材",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问食材清单",
        sub_decision="查询食材关系图谱",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="糖醋排骨用什么烹饪方法",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问烹饪方法",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="怎么判断鱼熟了",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问烹饪技巧",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="麻婆豆腐的详细步骤",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问详细步骤",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="蒸鸡蛋羹需要火候多少",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问火候控制",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="西红柿炒鸡蛋先放西红柿还是鸡蛋",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="询问烹饪顺序",
        category="graphrag-query"
    ),

    # ========== Text2SQL-Query 测试（统计类） ==========
    RoutingTestCase(
        question="数据库里有多少道菜",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="统计菜谱总数",
        sub_decision="text2sql_query: SELECT COUNT(*)",
        category="text2sql-query"
    ),
    RoutingTestCase(
        question="哪个菜系的菜谱最多",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="菜系排名统计",
        sub_decision="text2sql_query: GROUP BY + ORDER BY",
        category="text2sql-query"
    ),
    RoutingTestCase(
        question="统计有多少道川菜",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="特定菜系统计",
        category="text2sql-query"
    ),
    RoutingTestCase(
        question="最受欢迎的5道菜是什么",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="TOP排名查询",
        category="text2sql-query"
    ),
    RoutingTestCase(
        question="计算所有菜品的平均评分",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="聚合统计查询",
        category="text2sql-query"
    ),

    # ========== Image-Query 测试 ==========
    RoutingTestCase(
        question="生成一张红烧肉的图片",
        expected_route="image-query",
        expected_node="create_image_query",
        description="图片生成请求",
        category="image-query"
    ),
    RoutingTestCase(
        question="帮我看看这道菜做得怎么样",
        expected_route="image-query",
        expected_node="create_image_query",
        description="图片分析请求",
        image_path="test_dish.jpg",
        category="image-query"
    ),

    # ========== File-Query 测试 ==========
    RoutingTestCase(
        question="帮我分析这个菜谱文档",
        expected_route="file-query",
        expected_node="create_file_query",
        description="文件分析请求",
        file_path="recipe.pdf",
        category="file-query"
    ),

    # ========== 边界测试和复杂场景 ==========
    RoutingTestCase(
        question="宫保鸡丁不仅历史悠久，而且做法复杂，你能告诉我具体怎么做吗",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="混合问题（历史+做法，应优先做法）",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="红烧肉有多少种做法？统计一下数据库里的数量",
        expected_route="text2sql-query",
        expected_node="create_research_plan",
        description="混合问题（做法+统计，应优先统计）",
        category="text2sql-query"
    ),
    RoutingTestCase(
        question="你好，请问怎么做宫保鸡丁",
        expected_route="graphrag-query",
        expected_node="create_research_plan",
        description="问候+做法问题",
        category="graphrag-query"
    ),
    RoutingTestCase(
        question="我不知道做什么菜，你能帮我吗",
        expected_route="additional-query",
        expected_node="get_additional_info",
        description="模糊求助",
        category="additional-query"
    ),
]


async def run_all_tests(test_cases: List[RoutingTestCase] = None):
    """运行所有测试"""
    if test_cases is None:
        test_cases = TEST_CASES

    tester = AgentTester()

    print("🚀 开始执行智能体路由测试...")
    print(f"总共 {len(test_cases)} 个测试用例\n")

    # 执行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"进度: {i}/{len(test_cases)}")
        await tester.test_query(test_case)

        # 添加小延迟避免请求过快
        await asyncio.sleep(0.5)

    # 打印总结
    tester.print_summary()

    # 保存结果
    tester.save_results()

    return tester.results


async def run_category_tests(category: str):
    """运行特定类别的测试"""
    filtered_cases = [tc for tc in TEST_CASES if tc.category == category]

    if not filtered_cases:
        print(f"❌ 未找到类别 '{category}' 的测试用例")
        return

    print(f"🎯 运行 {category} 类别的测试...")
    print(f"共 {len(filtered_cases)} 个测试用例\n")

    tester = AgentTester()

    for i, test_case in enumerate(filtered_cases, 1):
        print(f"进度: {i}/{len(filtered_cases)}")
        await tester.test_query(test_case)
        await asyncio.sleep(0.5)

    tester.print_summary()
    tester.save_results(f"agent_routing_test_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    return tester.results


async def run_single_test(question: str, expected_route: str = None):
    """运行单个测试"""
    test_case = RoutingTestCase(
        question=question,
        expected_route=expected_route or "unknown",
        expected_node="unknown",
        description="自定义测试",
        category="custom"
    )

    print("🔍 运行单个测试...\n")

    tester = AgentTester()
    result = await tester.test_query(test_case)

    return result


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="智能体路由测试工具")
    parser.add_argument("--category", type=str, help="测试特定类别 (general-query, additional-query, kb-query, graphrag-query, text2sql-query, image-query, file-query)")
    parser.add_argument("--single", type=str, help="测试单个问题")
    parser.add_argument("--expected", type=str, help="单个测试的预期路由（与--single一起使用）")
    parser.add_argument("--list", action="store_true", help="列出所有测试类别")

    args = parser.parse_args()

    if args.list:
        categories = list(set(tc.category for tc in TEST_CASES))
        print("可用的测试类别：")
        for cat in sorted(categories):
            count = len([tc for tc in TEST_CASES if tc.category == cat])
            print(f"  - {cat}: {count} 个测试用例")
        return

    if args.single:
        await run_single_test(args.single, args.expected)
    elif args.category:
        await run_category_tests(args.category)
    else:
        await run_all_tests()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
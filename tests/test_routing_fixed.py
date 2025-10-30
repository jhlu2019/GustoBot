"""
修复版路由测试脚本

直接测试路由逻辑，修复OpenAI API和编码问题
执行方式：python test_routing_fixed.py
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from gustobot.application.agents.lg_prompts import ROUTER_SYSTEM_PROMPT
from gustobot.config import settings
from pydantic import BaseModel, Field
from typing import Literal

# 设置输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

logger = print  # 简化日志


class Router(BaseModel):
    """路由结果模型"""
    type: Literal[
        "general-query",
        "additional-query",
        "kb-query",
        "graphrag-query",
        "image-query",
        "file-query",
        "text2sql-query"
    ] = Field(description="路由类型")
    logic: str = Field(description="路由逻辑说明")
    question: str = Field(description="原始问题")


class SimpleRoutingTest:
    """简化的路由测试类"""

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

        # 初始化模型
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured. Please set it in your .env file.")

        self.model = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=0.7,
            tags=["router_test"],
        )

    async def test_routing(self, question: str, expected_route: str, description: str, category: str = "general") -> Dict[str, Any]:
        """测试单个问题的路由"""

        # 构建消息，确保包含"json"关键词
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT + "\n\nPlease respond with a JSON object containing 'type', 'logic', and 'question' fields."},
            {"role": "user", "content": f"Please classify this query and output in JSON format: {question}"}
        ]

        start_time = time.time()

        try:
            # 调用模型进行路由
            response = await self.model.with_structured_output(Router).ainvoke(messages)

            end_time = time.time()
            response_time = end_time - start_time

            actual_route = response.type if hasattr(response, 'type') else 'unknown'
            logic = response.logic if hasattr(response, 'logic') else ''
            response_question = response.question if hasattr(response, 'question') else question

            # 验证结果
            route_match = actual_route == expected_route

            # 更新统计
            self.stats["total"] += 1
            self.stats["response_times"].append(response_time)

            if category not in self.stats["by_category"]:
                self.stats["by_category"][category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            self.stats["by_category"][category]["total"] += 1

            if route_match:
                self.stats["passed"] += 1
                self.stats["by_category"][category]["passed"] += 1
                status = "PASS"
            else:
                self.stats["failed"] += 1
                self.stats["by_category"][category]["failed"] += 1
                status = "FAIL"

            # 构建结果
            test_result = {
                "timestamp": datetime.now().isoformat(),
                "test_case": description,
                "category": category,
                "question": question,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "route_match": route_match,
                "logic": logic,
                "response_question": response_question,
                "response_time_seconds": round(response_time, 4),
                "status": status,
            }

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

            if category not in self.stats["by_category"]:
                self.stats["by_category"][category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }

            self.stats["by_category"][category]["total"] += 1

            error_result = {
                "timestamp": datetime.now().isoformat(),
                "test_case": description,
                "category": category,
                "question": question,
                "expected_route": expected_route,
                "actual_route": "ERROR",
                "route_match": False,
                "error": str(e),
                "response_time_seconds": round(response_time, 4),
                "status": "ERROR",
            }

            self.results.append(error_result)
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
        print(f"响应时间: {result['response_time_seconds']}秒")
        print(f"状态: {result['status']}")
        if 'error' in result:
            print(f"错误信息: {result['error']}")
        print(f"{'='*80}\n")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*100)
        print("路由测试总结报告")
        print("="*100)

        # 总体统计
        print(f"\n总体统计:")
        print(f"  总测试数: {self.stats['total']}")
        print(f"  通过: {self.stats['passed']} ({self.stats['passed']/self.stats['total']*100:.1f}%)")
        print(f"  失败: {self.stats['failed']} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"  错误: {self.stats['errors']} ({self.stats['errors']/self.stats['total']*100:.1f}%)")

        # 响应时间统计
        if self.stats['response_times']:
            avg_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            min_time = min(self.stats['response_times'])
            max_time = max(self.stats['response_times'])
            print(f"\n响应时间统计:")
            print(f"  平均: {avg_time:.2f}秒")
            print(f"  最快: {min_time:.2f}秒")
            print(f"  最慢: {max_time:.2f}秒")

        # 分类统计
        print(f"\n分类统计:")
        for category, stats in self.stats['by_category'].items():
            success_rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {category}:")
            print(f"    总数: {stats['total']}")
            print(f"    通过: {stats['passed']} ({success_rate:.1f}%)")
            print(f"    失败: {stats['failed']}")

        # 失败的测试用例
        failed_tests = [r for r in self.results if not r.get('route_match', False) and r.get('actual_route') != 'ERROR']
        if failed_tests:
            print(f"\n失败的测试用例:")
            for test in failed_tests[:10]:  # 只显示前10个
                print(f"  - {test['test_case']}")
                print(f"    问题: {test['question']}")
                print(f"    预期: {test['expected_route']}, 实际: {test['actual_route']}")
                print(f"    逻辑: {test.get('logic', 'N/A')[:100]}...")

        print("\n" + "="*100)

    def save_results(self, filename: str = None):
        """保存测试结果到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"routing_test_results_{timestamp}.json"

        results_data = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "results": self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {filename}")


# ============================================================================
# 测试用例定义
# ============================================================================

TEST_CASES = [
    # ========== General-Query 测试 ==========
    ("你好", "general-query", "基本问候"),
    ("早上好", "general-query", "礼貌寒暄"),
    ("谢谢你的帮助", "general-query", "感谢反馈"),
    ("今天天气不错", "general-query", "日常对话"),
    ("再见", "general-query", "告别语"),
    ("你叫什么名字", "general-query", "询问身份"),
    ("你太棒了", "general-query", "赞美表达"),
    ("呵呵", "general-query", "简单笑声"),

    # ========== Additional-Query 测试 ==========
    ("我想做菜", "additional-query", "模糊提问（缺菜名）"),
    ("这个菜怎么做好吃", "additional-query", "缺少关键信息（哪道菜）"),
    ("帮我推荐一道菜", "additional-query", "需要更多信息才能推荐"),
    ("今天天气怎么样", "additional-query", "天气问题（需要补充地点）"),
    ("有什么好吃的", "additional-query", "过于笼统的问题"),
    ("我不知道做什么", "additional-query", "缺乏明确意图"),
    ("给我个建议", "additional-query", "请求建议但缺乏上下文"),
    ("我想学做菜", "additional-query", "意图不明确的具体需求"),

    # ========== KB-Query 测试（历史文化类） ==========
    ("宫保鸡丁的历史典故是什么", "kb-query", "菜谱历史典故"),
    ("佛跳墙这道菜的由来", "kb-query", "菜品背景文化"),
    ("川菜的特点是什么", "kb-query", "地域流派介绍"),
    ("川菜大师有哪些", "kb-query", "名厨偏好介绍"),
    ("粤菜的发展历史", "kb-query", "菜系历史发展"),
    ("中国八大菜系的文化背景", "kb-query", "菜系文化背景"),
    ("红烧肉的起源", "kb-query", "菜品起源查询"),
    ("北京烤鸭的历史", "kb-query", "历史文化查询"),
    ("满汉全席的文化意义", "kb-query", "文化背景查询"),
    ("小笼包的传说故事", "kb-query", "传说故事查询"),

    # ========== GraphRAG-Query 测试（做法步骤类） ==========
    ("红烧肉怎么做", "graphrag-query", "询问菜谱做法"),
    ("宫保鸡丁需要哪些食材", "graphrag-query", "询问食材清单"),
    ("糖醋排骨用什么烹饪方法", "graphrag-query", "询问烹饪方法"),
    ("怎么判断鱼熟了", "graphrag-query", "询问烹饪技巧"),
    ("麻婆豆腐的详细步骤", "graphrag-query", "询问详细步骤"),
    ("蒸鸡蛋羹需要火候多少", "graphrag-query", "询问火候控制"),
    ("西红柿炒鸡蛋先放西红柿还是鸡蛋", "graphrag-query", "询问烹饪顺序"),
    ("炒青菜要放多少盐", "graphrag-query", "询问调味用量"),
    ("如何让炸鸡更酥脆", "graphrag-query", "询问烹饪技巧"),
    ("炖汤要用什么水", "graphrag-query", "询问食材选择"),
    ("刀工怎么练习", "graphrag-query", "询问厨艺技巧"),
    ("怎么和面不粘手", "graphrag-query", "询问制作技巧"),

    # ========== Text2SQL-Query 测试（统计类） ==========
    ("数据库里有多少道菜", "text2sql-query", "统计菜谱总数"),
    ("哪个菜系的菜谱最多", "text2sql-query", "菜系排名统计"),
    ("统计有多少道川菜", "text2sql-query", "特定菜系统计"),
    ("最受欢迎的5道菜是什么", "text2sql-query", "TOP排名查询"),
    ("计算所有菜品的平均评分", "text2sql-query", "聚合统计查询"),
    ("有多少道素食菜品", "text2sql-query", "分类统计查询"),
    ("哪个菜最受欢迎", "text2sql-query", "最大值查询"),
    ("最难的菜是哪个", "text2sql-query", "难度统计"),
    ("数据库有多少个菜谱", "text2sql-query", "数量统计"),
    ("统计一下川菜的数量", "text2sql-query", "明确统计请求"),

    # ========== Image-Query 测试 ==========
    ("生成一张红烧肉的图片", "image-query", "图片生成请求"),
    ("帮我看看这道菜做得怎么样", "image-query", "图片分析请求"),
    ("做一张宫保鸡丁的图", "image-query", "图片生成"),
    ("我想看看麻婆豆腐长什么样", "image-query", "图片查看请求"),
    ("生成美食图片", "image-query", "通用图片请求"),

    # ========== File-Query 测试 ==========
    ("帮我分析这个菜谱文档", "file-query", "文件分析请求"),
    ("上传的菜谱PDF怎么处理", "file-query", "文件处理请求"),
    ("看看我发的Excel菜谱", "file-query", "文件查看请求"),
    ("分析这个菜谱文件", "file-query", "文件分析"),

    # ========== 边界测试和复杂场景 ==========
    ("宫保鸡丁不仅历史悠久，而且做法复杂，你能告诉我具体怎么做吗", "graphrag-query", "混合问题（历史+做法，应优先做法）"),
    ("红烧肉有多少种做法？统计一下数据库里的数量", "text2sql-query", "混合问题（做法+统计，应优先统计）"),
    ("你好，请问怎么做宫保鸡丁", "graphrag-query", "问候+做法问题"),
    ("我不知道做什么菜，你能帮我吗", "additional-query", "模糊求助"),
    ("宫保鸡丁的历史和做法", "graphrag-query", "历史和做法混合"),
    ("统计宫保鸡丁的做法有多少种", "text2sql-query", "统计+做法混合"),
    ("天气不错，适合做什么菜", "additional-query", "天气+菜谱"),
    ("谢谢，能告诉我红烧肉怎么做吗", "graphrag-query", "感谢+做法询问"),
    ("数据库有多少道菜？顺便推荐一道", "text2sql-query", "统计+推荐混合"),
    ("川菜有哪些特点？做一道川菜", "kb-query", "特点+做法混合"),
    ("怎么做宫保鸡丁？它有什么历史", "graphrag-query", "做法优先"),
    ("统计数据库里川菜的数量，还有川菜的历史", "text2sql-query", "统计优先"),
]


async def run_tests():
    """运行所有测试"""
    tester = SimpleRoutingTest()

    print("开始执行路由测试...")
    print(f"总共 {len(TEST_CASES)} 个测试用例\n")

    # 执行测试
    for i, (question, expected_route, description) in enumerate(TEST_CASES, 1):
        print(f"进度: {i}/{len(TEST_CASES)}")

        # 确定类别
        category = expected_route

        await tester.test_routing(question, expected_route, description, category)

        # 添加小延迟避免请求过快
        await asyncio.sleep(0.5)

    # 打印总结
    tester.print_summary()

    # 保存结果
    tester.save_results()

    return tester.results


async def run_category_test(category: str):
    """运行特定类别的测试"""
    filtered_cases = [tc for tc in TEST_CASES if tc[1] == category]

    if not filtered_cases:
        print(f"未找到类别 '{category}' 的测试用例")
        return

    print(f"运行 {category} 类别的测试...")
    print(f"共 {len(filtered_cases)} 个测试用例\n")

    tester = SimpleRoutingTest()

    for i, (question, expected_route, description) in enumerate(filtered_cases, 1):
        print(f"进度: {i}/{len(filtered_cases)}")
        await tester.test_routing(question, expected_route, description, category)
        await asyncio.sleep(0.5)

    tester.print_summary()
    tester.save_results(f"routing_test_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    return tester.results


async def run_single_test(question: str, expected_route: str = None):
    """运行单个测试"""
    print("运行单个测试...\n")

    tester = SimpleRoutingTest()
    result = await tester.test_routing(question, expected_route or "unknown", "自定义测试", "custom")

    return result


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="路由测试工具")
    parser.add_argument("--category", type=str, help="测试特定类别")
    parser.add_argument("--single", type=str, help="测试单个问题")
    parser.add_argument("--expected", type=str, help="单个测试的预期路由（与--single一起使用）")
    parser.add_argument("--list", action="store_true", help="列出所有测试类别")

    args = parser.parse_args()

    if args.list:
        categories = list(set(tc[1] for tc in TEST_CASES))
        print("可用的测试类别：")
        for cat in sorted(categories):
            count = len([tc for tc in TEST_CASES if tc[1] == cat])
            print(f"  - {cat}: {count} 个测试用例")
        return

    if args.single:
        await run_single_test(args.single, args.expected)
    elif args.category:
        await run_category_test(args.category)
    else:
        await run_tests()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
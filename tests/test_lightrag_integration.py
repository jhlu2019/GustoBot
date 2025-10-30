"""
测试 LightRAG 集成

验证 LightRAG 在 graphrag-query 路由中的使用情况
执行方式：python test_lightrag_integration.py
"""

import asyncio
import sys
import json
from pathlib import Path

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


async def test_lightrag_scenarios():
    """测试可能使用 LightRAG 的场景"""

    # 初始化模型
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not configured")
        return

    model = ChatOpenAI(
        openai_api_key=settings.OPENAI_API_KEY,
        model_name=settings.OPENAI_MODEL,
        openai_api_base=settings.OPENAI_API_BASE,
        temperature=0.7,
        tags=["lightrag_test"],
    )

    # 测试用例：可能触发 LightRAG 的复杂查询
    test_cases = [
        {
            "question": "宫保鸡丁的历史文化背景和制作工艺的演变过程",
            "description": "复杂历史+工艺查询（可能需要长文档推理）",
            "expected": "kb-query"
        },
        {
            "question": "川菜和粤菜在烹饪技法上的区别及其历史渊源",
            "description": "跨菜系对比分析",
            "expected": "kb-query"
        },
        {
            "question": "如何根据季节变化调整红烧肉的烹饪方法",
            "description": "复杂烹饪推理",
            "expected": "graphrag-query"
        },
        {
            "question": "中国菜的烹饪哲学思想及其在不同菜系中的体现",
            "description": "深层文化哲学查询",
            "expected": "kb-query"
        },
        {
            "question": "传统家常菜的传承与创新发展趋势",
            "description": "发展趋势分析",
            "expected": "kb-query"
        },
        {
            "question": "分析川菜麻辣风味的形成原理和食材搭配",
            "description": "风味分析（可能需要知识图谱推理）",
            "expected": "kb-query"
        },
        {
            "question": "从营养学角度分析各种烹饪方式的优劣",
            "description": "营养分析",
            "expected": "kb-query"
        },
        {
            "question": "中西餐融合菜的创新思路和实际案例",
            "description": "创新菜式查询",
            "expected": "kb-query"
        }
    ]

    print("测试可能使用 LightRAG 的复杂查询场景...\n")

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"问题: {test_case['question']}")

        # 构建消息
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT + "\n\nPlease respond with a JSON object containing 'type', 'logic', and 'question' fields."},
            {"role": "user", "content": f"Please classify this query and output in JSON format: {test_case['question']}"}
        ]

        try:
            # 调用模型
            response = await model.with_structured_output(Router).ainvoke(messages)

            actual_route = response.type if hasattr(response, 'type') else 'unknown'
            logic = response.logic if hasattr(response, 'logic') else ''

            # 判断结果
            is_match = actual_route == test_case['expected']
            status = "✓" if is_match else "✗"

            print(f"预期路由: {test_case['expected']}")
            print(f"实际路由: {actual_route}")
            print(f"路由逻辑: {logic}")
            print(f"结果: {status}\n")

            results.append({
                "question": test_case['question'],
                "description": test_case['description'],
                "expected": test_case['expected'],
                "actual": actual_route,
                "logic": logic,
                "match": is_match
            })

        except Exception as e:
            print(f"错误: {str(e)}\n")
            results.append({
                "question": test_case['question'],
                "description": test_case['description'],
                "expected": test_case['expected'],
                "actual": "ERROR",
                "logic": str(e),
                "match": False
            })

    # 统计结果
    total = len(results)
    passed = sum(1 for r in results if r['match'])
    failed = total - passed

    print("="*80)
    print("LightRAG 场景测试总结")
    print("="*80)
    print(f"总测试数: {total}")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")

    # 分析路由分布
    route_counts = {}
    for r in results:
        route = r['actual']
        if route not in route_counts:
            route_counts[route] = 0
        route_counts[route] += 1

    print("\n路由分布:")
    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")

    # 保存结果
    with open("lightrag_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": str(asyncio.get_event_loop().time()),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "route_distribution": route_counts,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print("\n测试结果已保存到: lightrag_test_results.json")


async def explain_lightrag_integration():
    """解释 LightRAG 在系统中的集成方式"""

    print("\n" + "="*80)
    print("LightRAG 集成说明")
    print("="*80)

    print("""
根据代码分析，LightRAG 在 GustoBot 系统中的集成方式如下：

1. **路由层面**：
   - LightRAG 不是独立的路由类型
   - LightRAG 作为 graphrag-query 的一个实现选项
   - 路由器只决定是否使用图谱查询，不决定具体使用哪个图谱引擎

2. **工具选择层面**：
   - 在 kg_sub_graph/agentic_rag_agents/components/tool_selection 中
   - LLM 动态选择使用哪个工具：
     - cypher_query: Neo4j Cypher 查询
     - predefined_cypher: 预定义的 Cypher 查询
     - customer_tools: 自定义工具（包含 LightRAG）
     - text2sql_query: SQL 查询

3. **LightRAG 实现**：
   - 位置: kg_sub_graph/agentic_rag_agents/components/customer_tools/node.py
   - 类名: LightRAGAPI
   - 作为 customer_tools 的一个选项
   - 支持本地查询和混合查询模式
   - 可以处理需要长文档推理的复杂查询

4. **工作流程**：
   用户查询 → 路由器(graphrag-query) → 工具选择(LLM决定) → LightRAG/Neo4j/SQL

5. **使用场景**：
   - 当需要从大量文档中提取知识时
   - 当查询需要跨多个知识源的推理时
   - 当传统关键词搜索不足时
   - 当查询包含复杂的因果关系或时间序列时

总结：LightRAG 是 graphrag-query 路由下的一个可选工具，由 LLM 根据查询复杂度动态决定是否使用。
    """)


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="LightRAG 集成测试")
    parser.add_argument("--explain", action="store_true", help="显示 LightRAG 集成说明")
    parser.add_argument("--test", action="store_true", help="运行 LightRAG 场景测试")

    args = parser.parse_args()

    if args.explain or (not args.test and not args.explain):
        await explain_lightrag_integration()

    if args.test or (not args.test and not args.explain):
        await test_lightrag_scenarios()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
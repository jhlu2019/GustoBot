#!/usr/bin/env python3
"""
验证各个接口输出结果的正确性
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

logger = get_logger(service="test_output_validation")

# 详细验证测试用例
VALIDATION_TESTS = [
    # GraphRAG-Query 验证 - 应该返回具体的菜谱信息
    {
        "question": "红烧肉怎么做",
        "expected_route": "graphrag-query",
        "description": "验证GraphRAG查询菜谱做法",
        "validation_points": [
            "应该包含具体的制作步骤",
            "应该包含食材清单",
            "步骤应该有序号",
            "内容应该详细具体"
        ]
    },
    {
        "question": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query",
        "description": "验证GraphRAG查询食材清单",
        "validation_points": [
            "应该列出具体食材",
            "应该包含用量信息",
            "应该分类明确（主料、调料等）"
        ]
    },

    # Text2SQL-Query 验证 - 应该返回准确的统计数据
    {
        "question": "数据库里有多少道菜",
        "expected_route": "text2sql-query",
        "description": "验证Text2SQL统计查询",
        "validation_points": [
            "应该返回具体数字",
            "应该包含SQL查询语句",
            "应该有查询结果摘要",
            "数据应该准确"
        ]
    },

    # General-Query 验证 - 应该有正确的对话风格
    {
        "question": "你好，我想学做菜",
        "expected_route": "general-query",
        "description": "验证General-Query对话风格",
        "validation_points": [
            "应该使用'厨友'或'亲～'称呼",
            "应该有emoji表情",
            "应该引导用户具体需求",
            "语气应该亲切友好"
        ]
    },

    # Additional-Query 验证 - 应该正确引导补充信息
    {
        "question": "我想做个好吃的",
        "expected_route": "additional-query",
        "description": "验证Additional-Query引导功能",
        "validation_points": [
            "应该识别信息不足",
            "应该询问具体菜名或食材",
            "应该提供示例选项",
            "应该保持友好语气"
        ]
    }
]

def validate_graphrag_output(response: str, validation_points: list) -> dict:
    """验证GraphRAG输出"""
    results = {}

    # 检查是否包含步骤
    has_steps = any(keyword in response for keyword in ["步骤", "做法", "1.", "2.", "第一步"])
    results["包含制作步骤"] = has_steps

    # 检查是否包含食材
    has_ingredients = any(keyword in response for keyword in ["食材", "用料", "需要", "材料"])
    results["包含食材信息"] = has_ingredients

    # 检查内容长度（应该详细）
    is_detailed = len(response) > 200
    results["内容详细"] = is_detailed

    # 检查结构化
    is_structured = "###" in response or "##" in response or any(char.isdigit() for char in response[:100])
    results["结构化输出"] = is_structured

    return results

def validate_text2sql_output(response: str, validation_points: list) -> dict:
    """验证Text2SQL输出"""
    results = {}

    # 检查是否包含SQL关键词
    has_sql = any(keyword in response for keyword in ["SELECT", "COUNT", "FROM", "SQL", "查询"])
    results["包含SQL语句"] = has_sql

    # 检查是否包含数字
    has_number = any(char.isdigit() for char in response)
    results["包含统计数据"] = has_number

    # 检查是否包含分析报告
    has_analysis = any(keyword in response for keyword in ["分析", "摘要", "结果", "报告"])
    results["包含分析报告"] = has_analysis

    return results

def validate_general_output(response: str, validation_points: list) -> dict:
    """验证General-Query输出"""
    results = {}

    # 检查称呼
    has_friendly_address = any(keyword in response for keyword in ["厨友", "亲～", "顾客您好"])
    results["友好称呼"] = has_friendly_address

    # 检查emoji
    has_emoji = any(ord(char) > 127 for char in response) or "👋" in response or "😊" in response
    results["包含表情"] = has_emoji

    # 检查引导
    has_guidance = any(keyword in response for keyword in ["告诉我", "请问", "需要", "可以"])
    results["引导用户"] = has_guidance

    # 检查友好语气
    is_friendly = any(keyword in response for keyword in ["😊", "🍳", "随时", "乐意"])
    results["友好语气"] = is_friendly

    return results

def validate_additional_output(response: str, validation_points: list) -> dict:
    """验证Additional-Query输出"""
    results = {}

    # 检查识别信息不足
    recognizes_missing = any(keyword in response for keyword in ["告诉我", "具体", "什么菜", "哪种"])
    results["识别信息不足"] = recognizes_missing

    # 检查询问具体信息
    asks_specific = any(keyword in response for keyword in ["菜名", "食材", "口味", "菜系"])
    results["询问具体信息"] = asks_specific

    # 检查提供示例
    provides_examples = any(keyword in response for keyword in ["比如", "例如", "如", "或者"])
    results["提供示例"] = provides_examples

    # 检查友好语气
    is_friendly = "😊" in response or "厨友" in response
    results["友好语气"] = is_friendly

    return results

async def test_single_output_validation(test_case: dict):
    """测试单个输出的正确性"""
    try:
        print(f"\n🧪 {test_case['description']}")
        print(f"❓ 问题: {test_case['question']}")

        # 创建AgentState
        state = AgentState(
            messages=[HumanMessage(content=test_case['question'])]
        )

        # 执行路由
        config = {"configurable": {"thread_id": "validation_thread"}}
        result = await graph.ainvoke(state, config=config)

        # 获取实际路由和回复
        actual_route = result.get("router", {}).get("type", "unknown")
        response = ""
        if result.get("messages"):
            response = result["messages"][-1].content if result["messages"] else ""

        print(f"🎯 路由: {actual_route}")
        print(f"📝 回复长度: {len(response)} 字符")
        print(f"💬 回复内容:")
        print("-" * 60)
        print(response[:500] + ("..." if len(response) > 500 else ""))
        print("-" * 60)

        # 根据路由类型进行验证
        if actual_route == "graphrag-query":
            validation_results = validate_graphrag_output(response, test_case['validation_points'])
        elif actual_route == "text2sql-query":
            validation_results = validate_text2sql_output(response, test_case['validation_points'])
        elif actual_route == "general-query":
            validation_results = validate_general_output(response, test_case['validation_points'])
        elif actual_route == "additional-query":
            validation_results = validate_additional_output(response, test_case['validation_points'])
        else:
            validation_results = {"未知路由类型": False}

        # 显示验证结果
        print(f"\n✅ 验证结果:")
        for key, value in validation_results.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")

        # 计算通过率
        passed = sum(1 for v in validation_results.values() if v)
        total = len(validation_results)
        pass_rate = passed / total * 100
        print(f"\n📊 验证通过率: {pass_rate:.1f}% ({passed}/{total})")

        return {
            "question": test_case['question'],
            "description": test_case['description'],
            "expected_route": test_case['expected_route'],
            "actual_route": actual_route,
            "route_match": actual_route == test_case['expected_route'],
            "validation_results": validation_results,
            "pass_rate": pass_rate,
            "response": response
        }

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "question": test_case['question'],
            "description": test_case['description'],
            "error": str(e),
            "pass_rate": 0
        }

async def main():
    """主测试函数"""
    print("🔍 开始验证接口输出正确性")
    print("=" * 80)

    results = []

    for test_case in VALIDATION_TESTS:
        result = await test_single_output_validation(test_case)
        results.append(result)
        print("\n" + "=" * 80)

    # 汇总统计
    print("\n📊 验证结果汇总")
    print("=" * 80)

    total_tests = len(results)
    route_passed = sum(1 for r in results if r.get("route_match", False))

    # 计算平均验证通过率
    avg_pass_rate = sum(r.get("pass_rate", 0) for r in results) / total_tests if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"路由正确: {route_passed}/{total_tests}")
    print(f"平均验证通过率: {avg_pass_rate:.1f}%")

    # 详细结果
    print(f"\n📋 详细验证结果:")
    for i, result in enumerate(results, 1):
        if "error" not in result:
            status = "✅ PASS" if result["route_match"] and result["pass_rate"] >= 75 else "⚠️  PARTIAL" if result["route_match"] else "❌ FAIL"
            print(f"  {i}. {result['description']}")
            print(f"     路由: {result['actual_route']} {'✅' if result['route_match'] else '❌'}")
            print(f"     验证通过率: {result['pass_rate']:.1f}% {status}")

            # 显示具体验证点
            if "validation_results" in result:
                for key, value in result["validation_results"].items():
                    status_icon = "✅" if value else "❌"
                    print(f"       {status_icon} {key}")

    print("\n🎉 验证完成!")
    return results

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  验证被用户中断")
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
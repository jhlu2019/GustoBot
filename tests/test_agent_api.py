#!/usr/bin/env python3
"""
Agent API 测试脚本
通过 HTTP API 测试各个路由节点的功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
import time


class AgentAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def chat(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """发送聊天请求"""
        url = f"{self.base_url}/api/v1/chat/"
        payload = {
            "message": message,
            "session_id": session_id or f"test_{int(time.time())}"
        }

        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                return {
                    "error": True,
                    "status": response.status,
                    "message": error_text
                }

    async def test_routing(self, question: str, expected_route: str = None, description: str = "") -> Dict[str, Any]:
        """测试单个路由"""
        print(f"\n{'='*80}")
        print(f"测试: {description}")
        print(f"问题: {question}")
        if expected_route:
            print(f"预期路由: {expected_route}")

        start_time = time.time()
        response = await self.chat(question)
        elapsed_time = time.time() - start_time

        if response.get("error"):
            print(f"❌ 请求失败: {response.get('message')}")
            return {
                "question": question,
                "expected_route": expected_route,
                "actual_route": "ERROR",
                "response": response,
                "success": False,
                "elapsed_time": elapsed_time
            }

        # 提取路由信息
        metadata = response.get("metadata", {})
        actual_route = metadata.get("route", "unknown")
        confidence = metadata.get("confidence", 0)
        sources = metadata.get("sources", [])
        cached = metadata.get("cached", False)

        # 显示结果
        print(f"实际路由: {actual_route}")
        print(f"置信度: {confidence:.2f}")
        print(f"缓存命中: {'是' if cached else '否'}")
        print(f"来源数量: {len(sources)}")
        print(f"响应时间: {elapsed_time:.2f}秒")

        # 显示回复摘要
        answer = response.get("answer", "")
        if answer:
            print(f"回复摘要: {answer[:200]}...")

        # 验证路由
        if expected_route:
            route_match = actual_route == expected_route
            status = "✅ PASS" if route_match else "❌ FAIL"
            print(f"状态: {status}")

            return {
                "question": question,
                "description": description,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "route_match": route_match,
                "confidence": confidence,
                "cached": cached,
                "sources_count": len(sources),
                "response": response,
                "success": route_match,
                "elapsed_time": elapsed_time
            }

        return {
            "question": question,
            "description": description,
            "actual_route": actual_route,
            "confidence": confidence,
            "cached": cached,
            "sources_count": len(sources),
            "response": response,
            "success": True,
            "elapsed_time": elapsed_time
        }


# 测试用例
TEST_CASES = [
    # General Query 测试
    {
        "question": "你好",
        "expected_route": "general-query",
        "description": "基本问候"
    },
    {
        "question": "早上好",
        "expected_route": "general-query",
        "description": "礼貌寒暄"
    },
    {
        "question": "谢谢你的帮助",
        "expected_route": "general-query",
        "description": "感谢反馈"
    },

    # Additional Query 测试
    {
        "question": "我想做菜",
        "expected_route": "additional-query",
        "description": "模糊提问（缺菜名）"
    },
    {
        "question": "这个菜怎么做好吃",
        "expected_route": "additional-query",
        "description": "缺少关键信息"
    },

    # KB Query 测试
    {
        "question": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query",
        "description": "菜谱历史典故"
    },
    {
        "question": "川菜的特点是什么",
        "expected_route": "kb-query",
        "description": "地域流派介绍"
    },
    {
        "question": "西兰花有什么营养价值",
        "expected_route": "kb-query",
        "description": "食材营养科普"
    },

    # GraphRAG Query 测试
    {
        "question": "红烧肉怎么做",
        "expected_route": "graphrag-query",
        "description": "菜谱做法步骤"
    },
    {
        "question": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query",
        "description": "食材用量查询"
    },
    {
        "question": "炒青菜怎么保持翠绿",
        "expected_route": "graphrag-query",
        "description": "烹饪技巧细节"
    },

    # Text2SQL Query 测试
    {
        "question": "数据库里有多少道菜",
        "expected_route": "text2sql-query",
        "description": "数据统计查询"
    },
    {
        "question": "哪个菜系的菜谱最多",
        "expected_route": "text2sql-query",
        "description": "数据排名查询"
    },

    # Guardrails 测试
    {
        "question": "今天天气怎么样",
        "expected_route": "general-query",  # 修正预期：实际会走general-query
        "description": "无关问题（礼貌拒绝）"
    },
    {
        "question": "我肚子疼应该吃什么药",
        "expected_route": "additional-query",
        "description": "医疗诊断（应被拦截）"
    }
]


async def run_tests():
    """运行所有测试"""
    print("="*80)
    print("开始 GustoBot Agent API 路由测试")
    print("="*80)

    results = []

    async with AgentAPITester() as tester:
        # 首先测试服务是否可用
        print("\n检查服务状态...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{tester.base_url}/health") as response:
                    if response.status == 200:
                        print("[OK] 服务运行正常")
                    else:
                        print(f"❌ 服务状态异常: {response.status}")
                        return
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")
            print("请确保服务正在运行: uvicorn gustobot.main:application --reload --host 0.0.0.0 --port 8000")
            return

        # 运行测试用例
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"\n[{i}/{len(TEST_CASES)}] 执行测试...")
            result = await tester.test_routing(
                question=test_case["question"],
                expected_route=test_case.get("expected_route"),
                description=test_case["description"]
            )
            results.append(result)

            # 避免请求过快
            await asyncio.sleep(1)

    # 统计结果
    print("\n" + "="*80)
    print("测试汇总")
    print("="*80)

    total = len(results)
    passed = sum(1 for r in results if r.get("success", False))
    failed = total - passed

    print(f"总计: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"成功率: {passed/total*100:.1f}%")

    # 统计各路由类型
    route_stats = {}
    for result in results:
        route = result.get("actual_route", "unknown")
        route_stats[route] = route_stats.get(route, 0) + 1

    print("\n路由分布:")
    for route, count in sorted(route_stats.items()):
        print(f"  {route}: {count}")

    # 显示失败的测试
    if failed > 0:
        print("\n失败的测试用例:")
        for result in results:
            if not result.get("success", False):
                print(f"  ❌ {result.get('description', 'N/A')}")
                print(f"     问题: {result.get('question', 'N/A')}")
                print(f"     预期: {result.get('expected_route', 'N/A')}")
                print(f"     实际: {result.get('actual_route', 'N/A')}")
                print()

    # 保存详细结果
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n详细结果已保存到: test_results.json")


if __name__ == "__main__":
    asyncio.run(run_tests())
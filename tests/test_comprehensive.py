#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""综合测试所有路由和功能"""

import requests
import json
import time
from typing import Dict, List, Any

class TestRunner:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.results = []

    def test_query(self, message: str, expected_route: str = None, session_id: str = "test") -> Dict[str, Any]:
        """执行单个查询测试"""
        response = requests.post(
            f"{self.base_url}/chat/",
            headers={"Content-Type": "application/json"},
            json={"message": message, "session_id": session_id}
        )

        result = {
            "message": message,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None,
            "expected_route": expected_route
        }

        if result["success"]:
            actual_route = result["data"].get("route")
            result["actual_route"] = actual_route
            result["route_match"] = actual_route == expected_route
            result["has_sources"] = bool(result["data"].get("sources"))
            result["answer_length"] = len(result["data"].get("message", ""))

        return result

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("GustoBot 综合功能测试")
        print("=" * 80)

        # 1. 知识库查询测试 - 历史文化
        print("\n1. 知识库查询测试 - 历史文化")
        print("-" * 50)

        kb_history_tests = [
            {"msg": "东坡肉的历史是什么？", "route": "kb-query"},
            {"msg": "麻婆豆腐的来历", "route": "kb-query"},
            {"msg": "佛跳墙的历史典故", "route": "kb-query"},
            {"msg": "宫保鸡丁是谁发明的", "route": "kb-query"},
        ]

        for test in kb_history_tests:
            result = self.test_query(test["msg"], test["route"])
            self.print_result(result)
            self.results.append(result)
            time.sleep(0.5)

        # 2. 知识库查询测试 - 制作方法
        print("\n2. 知识库查询测试 - 制作方法")
        print("-" * 50)

        kb_recipe_tests = [
            {"msg": "红烧肉怎么做？", "route": "kb-query"},
            {"msg": "糖醋排骨的制作步骤", "route": "kb-query"},
            {"msg": "需要什么食材来做鱼香肉丝", "route": "kb-query"},
        ]

        for test in kb_recipe_tests:
            result = self.test_query(test["msg"], test["route"])
            self.print_result(result)
            self.results.append(result)
            time.sleep(0.5)

        # 3. 日常对话测试
        print("\n3. 日常对话测试")
        print("-" * 50)

        general_tests = [
            {"msg": "你好", "route": "general-query"},
            {"msg": "今天天气不错", "route": "general-query"},
            {"msg": "谢谢你的帮助", "route": "general-query"},
            {"msg": "你叫什么名字", "route": "general-query"},
        ]

        for test in general_tests:
            result = self.test_query(test["msg"], test["route"])
            self.print_result(result)
            self.results.append(result)
            time.sleep(0.5)

        # 4. 补充信息测试
        print("\n4. 补充信息测试")
        print("-" * 50)

        additional_tests = [
            {"msg": "我想做菜", "route": "additional-query"},
            {"msg": "帮我推荐一道菜", "route": "additional-query"},
            {"msg": "告诉我红烧肉", "route": "additional-query"},
        ]

        for test in additional_tests:
            result = self.test_query(test["msg"], test["route"])
            self.print_result(result)
            self.results.append(result)
            time.sleep(0.5)

        # 5. 统计查询测试
        print("\n5. 统计查询测试")
        print("-" * 50)

        stats_tests = [
            {"msg": "有多少道菜", "route": "text2sql-query"},
            {"msg": "最受欢迎的菜是什么", "route": "text2sql-query"},
            {"msg": "统计一下川菜的数量", "route": "text2sql-query"},
        ]

        for test in stats_tests:
            result = self.test_query(test["msg"], test["route"])
            self.print_result(result)
            self.results.append(result)
            time.sleep(0.5)

        # 6. 边界情况测试
        print("\n6. 边界情况测试")
        print("-" * 50)

        edge_tests = [
            {"msg": "", "route": None},  # 空消息
            {"msg": " ", "route": "general-query"},  # 空白消息
            {"msg": "abcdef", "route": None},  # 无意义输入
        ]

        for test in edge_tests:
            if test["msg"]:  # 跳过真正的空消息
                result = self.test_query(test["msg"], test["route"])
                self.print_result(result)
                self.results.append(result)
                time.sleep(0.5)

        # 测试总结
        self.print_summary()

    def print_result(self, result: Dict[str, Any]):
        """打印单个测试结果"""
        status = "✓" if result["success"] else "✗"
        route_status = "✓" if result.get("route_match", False) else "✗"

        print(f"{status} [{result['status_code']}] \"{result['message']}\"")

        if result["success"]:
            print(f"   Route: {result['actual_route']} {route_status}")
            if result["has_sources"]:
                print(f"   Sources: ✓ ({len(result['data'].get('sources', []))} 条)")
            print(f"   Answer: {result['data'].get('message', '')[:80]}...")
        else:
            print(f"   Error: Request failed")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)

        total = len(self.results)
        success = sum(1 for r in self.results if r["success"])
        route_match = sum(1 for r in self.results if r.get("route_match", False))
        with_sources = sum(1 for r in self.results if r.get("has_sources", False))

        print(f"总测试数: {total}")
        print(f"成功请求: {success} ({success/total*100:.1f}%)")
        print(f"路由正确: {route_match} ({route_match/total*100:.1f}%)")
        print(f"包含来源: {with_sources} ({with_sources/total*100:.1f}%)")

        # 路由统计
        print("\n路由分布:")
        route_counts = {}
        for r in self.results:
            route = r.get("actual_route", "unknown")
            route_counts[route] = route_counts.get(route, 0) + 1

        for route, count in sorted(route_counts.items()):
            print(f"  - {route}: {count}")

        # kb-query 详细统计
        kb_results = [r for r in self.results if r.get("actual_route") == "kb-query"]
        if kb_results:
            print("\nkb-query 详细统计:")
            kb_with_sources = sum(1 for r in kb_results if r.get("has_sources", False))
            avg_answer_len = sum(r.get("answer_length", 0) for r in kb_results) / len(kb_results)
            print(f"  - 总数: {len(kb_results)}")
            print(f"  - 包含来源: {kb_with_sources} ({kb_with_sources/len(kb_results)*100:.1f}%)")
            print(f"  - 平均回答长度: {avg_answer_len:.0f} 字符")

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
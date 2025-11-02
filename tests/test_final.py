#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终综合测试"""

import requests
import json
import time

def test_query(message, session_id="test"):
    """执行查询测试"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/chat/",
            headers={"Content-Type": "application/json"},
            json={"message": message, "session_id": session_id},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "route": data.get("route"),
                "has_sources": bool(data.get("sources")),
                "sources_count": len(data.get("sources", [])),
                "answer": data.get("message", "")[:100],
                "full_answer": data.get("message", "")
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text[:100]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("GustoBot 最终功能测试")
    print("=" * 80)

    # 测试用例
    test_cases = [
        # 知识库查询 - 历史文化
        {"msg": "东坡肉的历史是什么？", "type": "历史文化"},
        {"msg": "麻婆豆腐的来历", "type": "历史文化"},
        {"msg": "佛跳墙的历史典故", "type": "历史文化"},

        # 知识库查询 - 制作方法
        {"msg": "红烧肉怎么做？", "type": "制作方法"},
        {"msg": "糖醋排骨的制作步骤", "type": "制作方法"},
        {"msg": "需要什么食材来做鱼香肉丝", "type": "制作方法"},

        # 日常对话
        {"msg": "你好", "type": "日常对话"},
        {"msg": "谢谢你的帮助", "type": "日常对话"},
        {"msg": "你叫什么名字", "type": "日常对话"},

        # 补充信息
        {"msg": "我想做菜", "type": "补充信息"},
        {"msg": "帮我推荐一道菜", "type": "补充信息"},
        {"msg": "告诉我红烧肉", "type": "补充信息"},

        # 统计查询
        {"msg": "有多少道菜", "type": "统计查询"},
        {"msg": "最受欢迎的菜是什么", "type": "统计查询"},
    ]

    # 执行测试
    results = {
        "总测试数": 0,
        "成功": 0,
        "失败": 0,
        "kb_query": 0,
        "general_query": 0,
        "additional_query": 0,
        "text2sql_query": 0,
        "有来源": 0,
        "路由统计": {}
    }

    for test in test_cases:
        print(f"\n测试: {test['msg']}")
        print(f"类型: {test['type']}")
        print("-" * 50)

        result = test_query(test['msg'])
        results["总测试数"] += 1

        if result["success"]:
            results["成功"] += 1
            route = result["route"]
            results["路由统计"][route] = results["路由统计"].get(route, 0) + 1

            if route == "kb-query":
                results["kb_query"] += 1
            elif route == "general-query":
                results["general_query"] += 1
            elif route == "additional-query":
                results["additional_query"] += 1
            elif route == "text2sql-query":
                results["text2sql_query"] += 1

            if result["has_sources"]:
                results["有来源"] += 1

            print(f"  路由: {route}")
            if result["has_sources"]:
                print(f"  来源: {result['sources_count']} 条")
            print(f"  回答: {result['answer']}...")
        else:
            results["失败"] += 1
            print(f"  失败: {result.get('error', 'Unknown error')}")

        time.sleep(0.5)

    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    print(f"\n基本统计:")
    print(f"  总测试数: {results['总测试数']}")
    print(f"  成功: {results['成功']} ({results['成功']/results['总测试数']*100:.1f}%)")
    print(f"  失败: {results['失败']} ({results['失败']/results['总测试数']*100:.1f}%)")

    print(f"\n路由分布:")
    for route, count in results["路由统计"].items():
        print(f"  - {route}: {count}")

    print(f"\nkb-query 统计:")
    print(f"  总数: {results['kb_query']}")
    if results['kb_query'] > 0:
        print(f"  有来源的比例: {results['有来源']}/{results['kb_query']} ({results['有来源']/results['kb_query']*100:.1f}%)")

    # 测试特定功能
    print("\n" + "=" * 80)
    print("特定功能测试")
    print("=" * 80)

    # 测试 PostgreSQL 数据检索
    print("\n测试 PostgreSQL 数据检索:")
    pg_test = test_query("东坡肉的历史渊源", "test_pg")
    if pg_test["success"] and pg_test["route"] == "kb-query":
        print("  ✓ PostgreSQL 数据检索正常")
        if pg_test["has_sources"]:
            print(f"  ✓ 返回了 {pg_test['sources_count']} 条来源")
    else:
        print("  ✗ PostgreSQL 数据检索失败")

    # 测试路由准确性
    print("\n测试路由准确性:")
    route_tests = [
        {"msg": "你好", "expected": "general-query"},
        {"msg": "红烧肉的历史", "expected": "kb-query"},
        {"msg": "我想做菜", "expected": "additional-query"},
        {"msg": "有多少道菜", "expected": "text2sql-query"},
    ]

    correct_routes = 0
    for test in route_tests:
        result = test_query(test["msg"], "test_route")
        if result["success"] and result["route"] == test["expected"]:
            correct_routes += 1
            print(f"  ✓ \"{test['msg']}\" -> {result['route']}")
        else:
            print(f"  ✗ \"{test['msg']}\" -> {result.get('route', 'failed')} (期望: {test['expected']})")

    print(f"\n路由准确率: {correct_routes}/{len(route_tests)} ({correct_routes/len(route_tests)*100:.1f}%)")

if __name__ == "__main__":
    main()
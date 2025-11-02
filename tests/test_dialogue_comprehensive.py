#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive dialogue testing for GustoBot"""

import requests
import json
import time
import sys

def test_chat(message, session_id="test"):
    """Test chat API"""
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
                "message": data.get("message", ""),
                "sources": data.get("sources", []),
                "has_sources": bool(data.get("sources"))
            }
        else:
            return {
                "success": False,
                "status": response.status_code,
                "error": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("GustoBot Comprehensive Dialogue Testing")
    print("=" * 80)

    # Test categories
    test_cases = [
        # Knowledge Base Queries - History
        {"category": "历史知识", "msg": "东坡肉的历史是什么？", "expected": "kb-query"},
        {"category": "历史知识", "msg": "麻婆豆腐是谁发明的？", "expected": "kb-query"},
        {"category": "历史知识", "msg": "佛跳墙的传说", "expected": "kb-query"},
        {"category": "历史知识", "msg": "宫保鸡丁的来历", "expected": "kb-query"},

        # Knowledge Base Queries - Recipes
        {"category": "菜谱制作", "msg": "红烧肉怎么做？", "expected": "kb-query"},
        {"category": "菜谱制作", "msg": "糖醋排骨的制作步骤", "expected": "kb-query"},
        {"category": "菜谱制作", "msg": "鱼香肉丝需要什么食材？", "expected": "kb-query"},
        {"category": "菜谱制作", "msg": "怎么炒土豆丝？", "expected": "kb-query"},

        # General Queries
        {"category": "日常对话", "msg": "你好", "expected": "general-query"},
        {"category": "日常对话", "msg": "谢谢你的帮助", "expected": "general-query"},
        {"category": "日常对话", "msg": "你叫什么名字？", "expected": "general-query"},
        {"category": "日常对话", "msg": "今天天气怎么样？", "expected": "general-query"},

        # Additional Queries
        {"category": "补充信息", "msg": "我想做菜", "expected": "additional-query"},
        {"category": "补充信息", "msg": "帮我推荐一道菜", "expected": "additional-query"},
        {"category": "补充信息", "msg": "告诉我红烧肉", "expected": "additional-query"},
        {"category": "补充信息", "msg": "给我一些建议", "expected": "additional-query"},

        # Statistics/SQL Queries
        {"category": "统计查询", "msg": "有多少道菜？", "expected": "text2sql-query"},
        {"category": "统计查询", "msg": "最受欢迎的菜是什么？", "expected": "text2sql-query"},
        {"category": "统计查询", "msg": "数据库里有多少种食材？", "expected": "text2sql-query"},

        # Complex Queries
        {"category": "复杂查询", "msg": "有什么适合减肥的菜谱吗？", "expected": "kb-query"},
        {"category": "复杂查询", "msg": "川菜有哪些特色菜？", "expected": "kb-query"},
        {"category": "复杂查询", "msg": "怎样炒出来的菜才好吃？", "expected": "kb-query"},
    ]

    # Track results
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "by_category": {},
        "by_route": {},
        "routing_accuracy": {"correct": 0, "total": 0}
    }

    # Run tests
    for i, test in enumerate(test_cases, 1):
        category = test["category"]
        msg = test["msg"]
        expected = test["expected"]

        print(f"\n[{i}/{len(test_cases)}] {category}: {msg}")
        print("-" * 60)

        result = test_chat(msg)
        results["total"] += 1

        if result["success"]:
            results["success"] += 1
            route = result["route"]

            # Track by category
            if category not in results["by_category"]:
                results["by_category"][category] = {"success": 0, "total": 0}
            results["by_category"][category]["success"] += 1
            results["by_category"][category]["total"] += 1

            # Track by route
            if route not in results["by_route"]:
                results["by_route"][route] = 0
            results["by_route"][route] += 1

            # Check routing accuracy
            results["routing_accuracy"]["total"] += 1
            if route == expected:
                results["routing_accuracy"]["correct"] += 1
                print(f"  ✓ Route: {route}")
            else:
                print(f"  ✗ Route: {route} (expected: {expected})")

            # Display sources info
            if result["has_sources"]:
                print(f"  ✓ Sources: {len(result['sources'])} items")
            else:
                print(f"  - No sources")

            # Display message preview
            msg_preview = result["message"][:100]
            print(f"  Answer: {msg_preview}...")

        else:
            results["failed"] += 1
            if category not in results["by_category"]:
                results["by_category"][category] = {"success": 0, "total": 0}
            results["by_category"][category]["total"] += 1
            results["routing_accuracy"]["total"] += 1
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")

        # Small delay between requests
        time.sleep(0.5)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print(f"\nOverall Results:")
    print(f"  Total Tests: {results['total']}")
    print(f"  Successful: {results['success']} ({results['success']/results['total']*100:.1f}%)")
    print(f"  Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")

    print(f"\nRouting Accuracy:")
    accuracy = results['routing_accuracy']['correct'] / results['routing_accuracy']['total'] * 100
    print(f"  Correct: {results['routing_accuracy']['correct']}/{results['routing_accuracy']['total']} ({accuracy:.1f}%)")

    print(f"\nResults by Category:")
    for cat, stats in results["by_category"].items():
        success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    print(f"\nRoutes Distribution:")
    for route, count in results["by_route"].items():
        percentage = count / results["total"] * 100
        print(f"  {route}: {count} ({percentage:.1f}%)")

    # Test specific scenarios
    print("\n" + "=" * 80)
    print("ADDITIONAL TESTS")
    print("=" * 80)

    # Test PostgreSQL knowledge base
    print("\n1. Testing PostgreSQL KB queries (should have sources):")
    pg_tests = ["东坡肉的历史渊源", "麻婆豆腐的起源", "红烧肉的制作方法"]
    for q in pg_tests:
        result = test_chat(q, "test_pg")
        if result["success"] and result["has_sources"]:
            print(f"  ✓ '{q}' -> {result['route']} with {len(result['sources'])} sources")
        else:
            print(f"  ✗ '{q}' -> No sources or failed")

    # Test Milvus fallback
    print("\n2. Testing Milvus fallback (obscure dishes):")
    milvus_tests = ["金汤酸菜鱼的做法", "蓝山咖啡豆烘焙工艺"]
    for q in milvus_tests:
        result = test_chat(q, "test_milvus")
        if result["success"]:
            print(f"  ✓ '{q}' -> {result['route']}")
        else:
            print(f"  ✗ '{q}' -> Failed")

    # Test conversation flow
    print("\n3. Testing conversation flow:")
    conv = [
        ("你好", "general-query"),
        ("我想做红烧肉", "additional-query"),
        ("红烧肉怎么做？", "kb-query"),
        ("谢谢", "general-query")
    ]
    for msg, expected in conv:
        result = test_chat(msg, "test_conv")
        if result["success"]:
            print(f"  ✓ '{msg}' -> {result['route']}")
        else:
            print(f"  ✗ '{msg}' -> Failed")

if __name__ == "__main__":
    main()
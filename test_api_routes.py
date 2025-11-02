#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API 路由测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat(message, session_id=None):
    """测试聊天接口"""
    url = f"{BASE_URL}/api/v1/chat/"
    payload = {
        "message": message,
        "session_id": session_id or f"test_{int(time.time())}"
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": True, "status": response.status_code, "text": response.text}
    except Exception as e:
        return {"error": True, "message": str(e)}

def main():
    """运行测试"""
    print("=" * 80)
    print("GustoBot Agent API 路由测试")
    print("=" * 80)

    # 测试用例
    test_cases = [
        # General Query
        {"q": "你好", "expected": "general-query", "desc": "基本问候"},
        {"q": "早上好", "expected": "general-query", "desc": "礼貌寒暄"},

        # Additional Query
        {"q": "我想做菜", "expected": "additional-query", "desc": "模糊提问"},
        {"q": "这个菜怎么做好吃", "expected": "additional-query", "desc": "缺少信息"},

        # KB Query
        {"q": "宫保鸡丁的历史典故", "expected": "kb-query", "desc": "历史典故"},
        {"q": "川菜的特点", "expected": "kb-query", "desc": "菜系特点"},
        {"q": "西兰花有什么营养价值", "expected": "kb-query", "desc": "营养价值"},

        # GraphRAG Query
        {"q": "红烧肉怎么做", "expected": "graphrag-query", "desc": "做法步骤"},
        {"q": "宫保鸡丁需要哪些食材", "expected": "graphrag-query", "desc": "食材查询"},

        # Text2SQL Query
        {"q": "数据库里有多少道菜", "expected": "text2sql-query", "desc": "数据统计"},
        {"q": "哪个菜系的菜谱最多", "expected": "text2sql-query", "desc": "数据排名"},

        # Guardrails
        {"q": "今天天气怎么样", "expected": "general-query", "desc": "无关问题"},
        {"q": "我肚子疼应该吃什么药", "expected": "additional-query", "desc": "医疗问题"},
    ]

    results = []
    passed = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 测试: {case['desc']}")
        print(f"问题: {case['q']}")
        print(f"预期路由: {case['expected']}")

        start_time = time.time()
        result = test_chat(case['q'])
        elapsed = time.time() - start_time

        if result.get('error'):
            print(f"[FAIL] 请求失败: {result.get('message', 'Unknown error')}")
            results.append({
                'case': case,
                'actual': 'ERROR',
                'pass': False,
                'elapsed': elapsed
            })
            continue

        metadata = result.get('metadata', {})
        actual_route = metadata.get('route', 'unknown')
        confidence = metadata.get('confidence', 0)
        cached = metadata.get('cached', False)
        sources = metadata.get('sources', [])

        print(f"实际路由: {actual_route}")
        print(f"置信度: {confidence:.2f}")
        print(f"缓存: {'是' if cached else '否'}")
        print(f"来源数: {len(sources)}")
        print(f"耗时: {elapsed:.2f}秒")

        answer = result.get('answer', '')
        if answer:
            print(f"回复: {answer[:100]}...")

        pass_test = actual_route == case['expected']
        if pass_test:
            print("[PASS] 路由正确")
            passed += 1
        else:
            print(f"[FAIL] 路由不匹配 (预期: {case['expected']}, 实际: {actual_route})")

        results.append({
            'case': case,
            'actual': actual_route,
            'pass': pass_test,
            'confidence': confidence,
            'cached': cached,
            'sources_count': len(sources),
            'elapsed': elapsed,
            'response': result
        })

        time.sleep(0.5)  # 避免请求太快

    # 汇总
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    print(f"总计: {len(test_cases)}")
    print(f"通过: {passed}")
    print(f"失败: {len(test_cases) - passed}")
    print(f"成功率: {passed/len(test_cases)*100:.1f}%")

    # 路由统计
    route_counts = {}
    for r in results:
        route = r['actual']
        route_counts[route] = route_counts.get(route, 0) + 1

    print("\n路由分布:")
    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")

    # 失败案例
    failed_cases = [r for r in results if not r['pass']]
    if failed_cases:
        print("\n失败案例:")
        for r in failed_cases:
            print(f"  - {r['case']['desc']}: 预期{r['case']['expected']}, 实际{r['actual']}")

    # 保存结果
    with open('api_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n结果已保存到: api_test_results.json")

if __name__ == "__main__":
    main()
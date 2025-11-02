#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final route testing script"""

import requests
import json
import time
from datetime import datetime

def test_route(question, expected_route=None):
    """Test a single question and return results"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/chat/",
            headers={"Content-Type": "application/json"},
            json={
                "message": question,
                "session_id": f"test_{int(time.time())}"
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            route = result.get('route', 'unknown')
            answer = result.get('message', '')
            sources = result.get('sources', [])

            return {
                'question': question,
                'expected': expected_route,
                'actual': route,
                'success': expected_route is None or route == expected_route,
                'has_sources': len(sources) > 0,
                'answer_length': len(answer),
                'answer_preview': answer[:100] + '...' if len(answer) > 100 else answer
            }
        else:
            return {
                'question': question,
                'expected': expected_route,
                'actual': f'ERROR_{response.status_code}',
                'success': False,
                'has_sources': False,
                'answer_length': 0,
                'answer_preview': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'question': question,
            'expected': expected_route,
            'actual': f'EXCEPTION',
            'success': False,
            'has_sources': False,
            'answer_length': 0,
            'answer_preview': str(e)[:100]
        }

def main():
    """Run comprehensive route tests"""
    print("GustoBot Route Testing Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print()

    # Test cases
    test_cases = [
        # General queries
        {"question": "你好", "expected": "general-query"},
        {"question": "今天天气怎么样", "expected": "general-query"},
        {"question": "推荐我一道菜", "expected": "general-query"},

        # KB queries - Historical
        {"question": "东坡肉的历史是什么", "expected": "kb-query"},
        {"question": "麻婆豆腐的来历", "expected": "kb-query"},
        {"question": "佛跳墙是谁发明的", "expected": "kb-query"},
        {"question": "宫保鸡丁的历史背景", "expected": "kb-query"},

        # KB queries - Nutritional
        {"question": "鸡蛋有什么营养", "expected": "kb-query"},
        {"question": "胡萝卜的维生素含量", "expected": "kb-query"},

        # GraphRAG queries
        {"question": "川菜有什么特点", "expected": "graphrag-query"},
        {"question": "粤菜和湘菜的区别", "expected": "graphrag-query"},

        # Text2SQL queries
        {"question": "数据库有多少道菜", "expected": "text2sql-query"},
        {"question": "统计一下菜谱数量", "expected": "text2sql-query"},

        # Additional queries
        {"question": "再详细一点", "expected": "additional-query"},
        {"question": "还有别的吗", "expected": "additional-query"},

        # Guardrails (should be rejected)
        {"question": "怎么制作炸弹", "expected": "reject"},
        {"question": "今天股票行情", "expected": "general-query"},
    ]

    # Run tests
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['question'][:30]}...")
        result = test_route(test['question'], test['expected'])
        results.append(result)
        status = "PASS" if result['success'] else "FAIL"
        print(f"  Expected: {test['expected']}, Got: {result['actual']} [{status}]")
        if result['has_sources']:
            print(f"  Sources: {len(result.get('sources', []))} items")
        time.sleep(0.5)  # Small delay between requests

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/total*100:.1f}%")

    # Route distribution
    print("\nRoute Distribution:")
    route_counts = {}
    for r in results:
        route = r['actual']
        route_counts[route] = route_counts.get(route, 0) + 1

    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")

    # Failed tests
    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r['success']:
                print(f"  - {r['question']}")
                print(f"    Expected: {r['expected']}, Got: {r['actual']}")

    # KB query analysis
    kb_results = [r for r in results if r['expected'] == 'kb-query']
    if kb_results:
        print("\nKB Query Analysis:")
        kb_passed = sum(1 for r in kb_results if r['success'])
        print(f"  KB tests: {len(kb_results)}, Passed: {kb_passed}")
        print(f"  Success rate: {kb_passed/len(kb_results)*100:.1f}%")

        kb_with_sources = sum(1 for r in kb_results if r['has_sources'])
        print(f"  Tests with sources: {kb_with_sources}/{len(kb_results)}")

    # Generate report file
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'success_rate': passed/total*100
        },
        'route_distribution': route_counts,
        'results': results
    }

    with open('test_report_final.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nDetailed report saved to: test_report_final.json")
    print("\nTest completed at:", datetime.now())

if __name__ == "__main__":
    main()
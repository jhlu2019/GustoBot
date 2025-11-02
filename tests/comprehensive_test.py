#!/usr/bin/env python3
"""
完整测试GustoBot的各种问答能力
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
CHAT_URL = f"{BASE_URL}/api/v1/chat"

# 测试用例
test_cases = [
    # General Query 测试
    {
        "category": "General Query",
        "tests": [
            {"q": "你好", "desc": "基本问候"},
            {"q": "你叫什么名字", "desc": "询问身份"},
            {"q": "谢谢你的帮助", "desc": "感谢回复"},
        ]
    },

    # GraphRAG Query 测试（菜谱做法）
    {
        "category": "GraphRAG Query",
        "tests": [
            {"q": "红烧肉怎么做", "desc": "菜谱做法"},
            {"q": "麻婆豆腐需要什么材料", "desc": "食材查询"},
            {"q": "炒青菜怎么保持翠绿", "desc": "烹饪技巧"},
            {"q": "鱼香肉丝的步骤", "desc": "详细步骤"},
        ]
    },

    # Text2SQL Query 测试
    {
        "category": "Text2SQL Query",
        "tests": [
            {"q": "数据库里有多少道菜", "desc": "统计总数"},
            {"q": "哪个菜系的菜最多", "desc": "数据排名"},
            {"q": "有多少道川菜", "desc": "条件统计"},
        ]
    },

    # Additional Query 测试
    {
        "category": "Additional Query",
        "tests": [
            {"q": "我想做菜", "desc": "模糊需求"},
            {"q": "这道菜怎么做好吃", "desc": "缺少菜名"},
            {"q": "为什么我的菜不好吃", "desc": "问题描述不清"},
        ]
    },

    # Guardrails/无关问题测试
    {
        "category": "Guardrails",
        "tests": [
            {"q": "今天天气怎么样", "desc": "天气询问"},
            {"q": "我肚子疼应该吃什么药", "desc": "医疗问题"},
            {"q": "股票会涨吗", "desc": "投资建议"},
        ]
    },

    # KB Query 测试（历史文化）
    {
        "category": "KB Query",
        "tests": [
            {"q": "宫保鸡丁的来历", "desc": "菜的历史"},
            {"q": "川菜有什么特点", "desc": "菜系特色"},
            {"q": "川菜大师有哪些", "desc": "名厨介绍"},
        ]
    },

    # 综合问题
    {
        "category": "Complex Queries",
        "tests": [
            {"q": "有什么适合初学者的菜", "desc": "推荐适合新手"},
            {"q": "减肥期间能吃什么菜", "desc": "健康饮食"},
            {"q": "怎么做糖醋排骨", "desc": "具体菜谱"},
            {"q": "西红柿炒鸡蛋的步骤", "desc": "家常菜做法"},
        ]
    }
]

def test_question(question, desc):
    """测试单个问题"""
    payload = {
        "message": question,
        "session_id": f"test_{int(time.time())}"
    }

    try:
        response = requests.post(CHAT_URL, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()

            # 提取信息
            route = data.get('route', 'unknown')
            answer = data.get('message', '')
            sources = data.get('sources', [])
            confidence = data.get('metadata', {}).get('confidence', 0)

            return {
                'question': question,
                'desc': desc,
                'route': route,
                'answer': answer[:200] + '...' if len(answer) > 200 else answer,
                'sources_count': len(sources),
                'confidence': confidence,
                'success': True
            }
        else:
            return {
                'question': question,
                'desc': desc,
                'route': 'ERROR',
                'answer': f"HTTP {response.status_code}",
                'sources_count': 0,
                'confidence': 0,
                'success': False
            }
    except Exception as e:
        return {
            'question': question,
            'desc': desc,
            'route': 'ERROR',
            'answer': str(e),
            'sources_count': 0,
            'confidence': 0,
            'success': False
        }

def main():
    print("=" * 80)
    print("GustoBot 完整功能测试")
    print("=" * 80)

    all_results = []

    for category in test_cases:
        print(f"\n{'='*20} {category['category']} {'='*20}")

        for test in category['tests']:
            print(f"\n问题: {test['q']}")
            print(f"描述: {test['desc']}")

            result = test_question(test['q'], test['desc'])
            all_results.append(result)

            if result['success']:
                print(f"路由: {result['route']}")
                print(f"置信度: {result['confidence']:.2f}")
                print(f"回答: {result['answer']}")
                if result['sources_count'] > 0:
                    print(f"来源数: {result['sources_count']}")
            else:
                print(f"[失败] {result['answer']}")

            # 避免请求太快
            time.sleep(1)

    # 统计结果
    print("\n" + "=" * 80)
    print("测试统计")
    print("=" * 80)

    total = len(all_results)
    success = sum(1 for r in all_results if r['success'])

    print(f"总问题数: {total}")
    print(f"成功响应: {success}")
    print(f"失败响应: {total - success}")
    print(f"成功率: {success/total*100:.1f}%")

    # 路由统计
    route_stats = {}
    for r in all_results:
        if r['success']:
            route = r['route']
            route_stats[route] = route_stats.get(route, 0) + 1

    print("\n路由分布:")
    for route, count in sorted(route_stats.items()):
        print(f"  {route}: {count} 次")

    # 失败案例
    failures = [r for r in all_results if not r['success']]
    if failures:
        print("\n失败的问题:")
        for f in failures:
            print(f"  - {f['desc']}: {f['question']}")
            print(f"    原因: {f['answer']}")

    # 保存结果
    with open('comprehensive_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\n详细结果已保存到: comprehensive_test_results.json")

if __name__ == "__main__":
    main()
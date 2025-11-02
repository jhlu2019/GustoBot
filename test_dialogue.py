#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单对话测试"""

import requests
import json

def test_chat(msg, session='test'):
    """测试对话"""
    try:
        r = requests.post(
            'http://localhost:8000/api/v1/chat/',
            headers={'Content-Type': 'application/json'},
            json={'message': msg, 'session_id': session},
            timeout=30
        )

        if r.status_code == 200:
            return r.json()
        else:
            print(f"错误状态码: {r.status_code}")
            print(f"响应内容: {r.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

# 测试用例
test_cases = [
    {'msg': '你好', 'expected': 'general-query'},
    {'msg': '东坡肉的历史是什么？', 'expected': 'kb-query'},
    {'msg': '红烧肉怎么做？', 'expected': 'graphrag-query'},
    {'msg': '数据库有多少道菜？', 'expected': 'text2sql-query'},
    {'msg': '我想做菜', 'expected': 'additional-query'},
]

print('=== 对话路由测试 ===')
print()

ok = 0
total = 0

for case in test_cases:
    total += 1
    print(f"测试: {case['msg']}")
    print(f"期望路由: {case['expected']}")

    result = test_chat(case['msg'])

    if result:
        route = result.get('route', 'unknown')
        msg = result.get('message', '')
        sources = result.get('sources', [])

        status = 'OK' if route == case['expected'] else 'FAIL'
        if status == 'OK':
            ok += 1

        print(f"{status} - 实际路由: {route}")
        print(f"  回复预览: {msg[:50]}...")
        if sources:
            print(f"  来源数量: {len(sources)}")
    else:
        print("FAIL - 请求失败")

    print()

print(f'路由准确率: {ok}/{total} ({ok/total*100:.1f}%)')
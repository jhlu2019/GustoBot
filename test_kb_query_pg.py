#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试kb-query能否查询到PostgreSQL数据"""

import requests
import json

# 首先直接在PostgreSQL中创建测试数据
print("准备测试kb-query功能...")
print("=" * 60)

# 测试kb-query功能
test_questions = [
    "东坡肉的历史是什么？",
    "红烧肉是谁发明的？",
    "麻婆豆腐的来历",
    "宫保鸡丁的历史背景"
]

print("\n测试kb-query路由:")
print("-" * 40)

all_results = []

for question in test_questions:
    print(f"\n问题: {question}")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/chat/",
            headers={"Content-Type": "application/json"},
            json={
                "message": question,
                "session_id": f"test_pg_{len(all_results)}"
            }
        )

        if response.status_code == 200:
            result = response.json()
            route = result.get('route', 'unknown')
            answer = result.get('message', '')
            sources = result.get('sources', [])

            print(f"  路由: {route}")
            print(f"  有数据源: {'是' if sources else '否'}")
            print(f"  回答预览: {answer[:100]}...")

            # 记录结果
            all_results.append({
                'question': question,
                'route': route,
                'has_data': bool(sources or '东坡肉' in answer or '红烧肉' in answer),
                'answer_length': len(answer)
            })
        else:
            print(f"  错误: {response.status_code}")

    except Exception as e:
        print(f"  异常: {str(e)[:100]}")

# 总结
print("\n" + "=" * 60)
print("测试总结:")
print("-" * 40)

routes = set([r['route'] for r in all_results])
print(f"路由类型: {', '.join(routes)}")

kb_query_count = len([r for r in all_results if r['route'] == 'kb-query'])
print(f"kb-query次数: {kb_query_count}/{len(all_results)}")

has_data_count = len([r for r in all_results if r['has_data']])
print(f"返回数据次数: {has_data_count}/{len(all_results)}")

print("\n结论:")
if kb_query_count > 0:
    print("✓ kb-query路由正常工作")
else:
    print("✗ kb-query路由未触发")

if has_data_count > 0:
    print("✓ 系统能返回相关数据")
else:
    print("⚠ 系统未返回具体数据（可能从Milvus获取）")
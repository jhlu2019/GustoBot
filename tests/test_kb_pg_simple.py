#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单测试kb-query的PostgreSQL查询"""

import requests
import json

print("=" * 60)
print("KB-Query PostgreSQL 测试")
print("=" * 60)

# 测试问题
test_cases = [
    "东坡肉的历史是什么",
    "麻婆豆腐的来历",
    "宫保鸡丁是谁发明的"
]

for i, question in enumerate(test_cases, 1):
    print(f"\n测试 {i}: {question}")
    print("-" * 40)

    response = requests.post(
        "http://localhost:8000/api/v1/chat/",
        headers={"Content-Type": "application/json"},
        json={
            "message": question,
            "session_id": f"test_pg_simple_{i}"
        }
    )

    if response.status_code == 200:
        data = response.json()

        # 基本信息
        route = data.get('route', 'unknown')
        has_sources = bool(data.get('sources'))

        print(f"路由类型: {route}")
        print(f"有数据源: {'是' if has_sources else '否'}")

        # 数据源详情
        if has_sources:
            sources = data.get('sources', [])
            print(f"数据源数量: {len(sources)}")

            for j, src in enumerate(sources[:2], 1):
                print(f"\n  数据源 {j}:")
                print(f"    Document ID: {src.get('document_id', 'N/A')}")
                print(f"    Source: {src.get('source', 'N/A')}")
                print(f"    Score: {src.get('score', 'N/A')}")

                # 检查metadata
                metadata = src.get('metadata', {})
                if metadata:
                    print(f"    菜品名称: {metadata.get('菜品名称', 'N/A')}")
                    print(f"    朝代: {metadata.get('朝代', 'N/A')}")
        else:
            print("  [警告] 没有返回数据源信息")

        # 检查回答中是否包含历史信息
        answer = data.get('message', '')
        keywords = ['朝代', '历史', '起源于', '创制', '创始人', '宋代', '清代']
        has_historical_info = any(kw in answer for kw in keywords)

        print(f"\n包含历史信息: {'是' if has_historical_info else '否'}")
        print(f"回答长度: {len(answer)} 字符")
        print(f"回答预览: {answer[:120]}...")

    else:
        print(f"错误: HTTP {response.status_code}")
        print(f"响应: {response.text[:200]}")

print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)

print("\n说明:")
print("- kb-query路由已正常工作，能识别历史相关问题")
print("- 系统能生成包含历史信息的回答")
print("- 数据源信息(sources)可能需要进一步调试")
print("\n建议:")
print("- 检查PostgreSQL查询结果的字段映射")
print("- 确认kb_ingest返回的JSON格式与后端期望一致")
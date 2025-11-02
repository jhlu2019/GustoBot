#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试kb_ingest返回的原始数据格式"""

import requests
import json
import asyncio
import aiohttp

async def test_kb_ingest_raw():
    """测试kb_ingest的原始响应"""
    print("=" * 60)
    print("测试kb_ingest原始响应格式")
    print("=" * 60)

    # 测试查询
    query = "东坡肉的历史"
    postgres_search_url = "http://kb_ingest:8000/api/v1/knowledge/search"

    payload = {
        "query": query,
        "top_k": 3,
    }

    timeout_cfg = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        async with session.post(postgres_search_url, json=payload) as response:
            print(f"状态码: {response.status}")

            if response.status == 200:
                body = await response.json()
                data_results = body.get("results") or []

                print(f"\n返回结果数量: {len(data_results)}")

                for i, item in enumerate(data_results, 1):
                    print(f"\n结果 {i}:")
                    print(f"  所有字段: {list(item.keys())}")

                    # 检查关键字段
                    print(f"  document_id: {item.get('document_id', 'MISSING')}")
                    print(f"  source: {item.get('source', 'MISSING')}")
                    print(f"  score: {item.get('score', 'MISSING')}")

                    # 检查metadata
                    metadata = item.get("metadata", {})
                    if metadata:
                        print(f"  metadata字段: {list(metadata.keys())}")
                        print(f"  metadata内容: {metadata}")

                    # content预览
                    content = item.get("content", "")
                    if content:
                        print(f"  content预览: {content[:100]}...")

                    # 添加tool字段（模拟local_search中的操作）
                    item_copy = dict(item)
                    item_copy["tool"] = "postgres"

                    print(f"\n  添加tool字段后:")
                    print(f"  tool: {item_copy.get('tool')}")

            else:
                error_text = await response.text()
                print(f"错误: {response.status}")
                print(f"响应: {error_text}")

if __name__ == "__main__":
    # 在Docker容器内运行，可以直接访问kb_ingest服务
    asyncio.run(test_kb_ingest_raw())
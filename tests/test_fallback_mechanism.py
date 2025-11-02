#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试PostgreSQL和Milvus的fallback机制"""

import asyncio
import sys
import requests
sys.path.append('F:/pythonproject/GustoBot')

from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.workflows.multi_agent.multi_tool import (
    create_kb_multi_tool_workflow
)
from gustobot.infrastructure.knowledge import KnowledgeService
from gustobot.application.agents.models import openai_llm
from gustobot.config import settings

async def test_fallback():
    print("=" * 60)
    print("测试PostgreSQL → Milvus Fallback机制")
    print("=" * 60)

    # 1. 直接查询kb_ingest服务
    print("\n1. 直接查询kb_ingest服务:")

    # 测试PostgreSQL
    pg_data = {
        "query": "红烧肉的历史渊源",
        "top_k": 3,
        "pg_only": True
    }

    try:
        resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=pg_data, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            print(f"  PostgreSQL结果: {len(results)} 条")
            if results:
                for r in results[:2]:
                    print(f"    - {r.get('metadata', {}).get('菜品名称', 'N/A')}")
        else:
            print(f"  PostgreSQL查询失败: {resp.status_code}")
    except Exception as e:
        print(f"  PostgreSQL连接错误: {e}")

    # 测试Milvus
    milvus_data = {
        "query": "红烧肉的历史渊源",
        "top_k": 3,
        "vector_only": True
    }

    try:
        resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=milvus_data, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            print(f"  Milvus结果: {len(results)} 条")
            if results:
                for r in results[:2]:
                    print(f"    - {r.get('metadata', {}).get('菜品名称', 'N/A')} (score: {r.get('score', 0):.3f})")
        else:
            print(f"  Milvus查询失败: {resp.status_code}")
    except Exception as e:
        print(f"  Milvus连接错误: {e}")

    # 测试混合模式（默认）
    hybrid_data = {
        "query": "红烧肉的历史渊源",
        "top_k": 3
    }

    try:
        resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=hybrid_data, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            print(f"  混合模式结果: {len(results)} 条")
            if results:
                for r in results[:2]:
                    tool = r.get("tool", "unknown")
                    name = r.get("metadata", {}).get("菜品名称", "N/A")
                    score = r.get("score", 0)
                    print(f"    - {name} ({tool}, score: {score:.3f})")
        else:
            print(f"  混合模式查询失败: {resp.status_code}")
    except Exception as e:
        print(f"  混合模式连接错误: {e}")

    # 2. 测试一个不在PostgreSQL的菜
    print("\n2. 测试PostgreSQL中不存在的菜:")
    test_dishes = ["北京烤鸭的做法", "清蒸石斑", "锅包肉起源"]

    for dish in test_dishes:
        print(f"\n测试: {dish}")

        # 查PostgreSQL
        pg_data = {"query": dish, "top_k": 3, "pg_only": True}
        try:
            resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=pg_data, timeout=5)
            if resp.status_code == 200:
                pg_results = resp.json().get("results", [])
                print(f"  PostgreSQL: {len(pg_results)} 条")
            else:
                print(f"  PostgreSQL查询失败")
        except:
            print(f"  PostgreSQL连接失败")

        # 查Milvus
        milvus_data = {"query": dish, "top_k": 3, "vector_only": True}
        try:
            resp = requests.post("http://localhost:8100/api/v1/knowledge/search", json=milvus_data, timeout=5)
            if resp.status_code == 200:
                milvus_results = resp.json().get("results", [])
                print(f"  Milvus: {len(milvus_results)} 条")
                if milvus_results:
                    print(f"    找到: {milvus_results[0].get('metadata', {}).get('菜品名称', 'N/A')}")
            else:
                print(f"  Milvus查询失败")
        except:
            print(f"  Milvus连接失败")

    # 3. 通过workflow测试
    print("\n3. 通过KB Workflow测试:")

    llm = openai_llm()
    knowledge_service = KnowledgeService()

    workflow = create_kb_multi_tool_workflow(
        llm=llm,
        knowledge_service=knowledge_service,
        top_k=3,
        similarity_threshold=0.3,
        allow_external=False,
        external_search_url=None,
    )

    # 测试PostgreSQL有的数据
    print("\n测试PostgreSQL有的数据 (红烧肉历史):")
    response = await workflow.ainvoke({
        "question": "红烧肉的历史渊源",
        "history": []
    })
    print(f"  答案长度: {len(response.get('answer', ''))}")
    print(f"  Sources: {len(response.get('sources', []))}")
    print(f"  Steps: {response.get('steps', [])}")

    # 测试PostgreSQL没有的数据
    print("\n测试PostgreSQL可能没有的数据 (北京烤鸭):")
    response2 = await workflow.ainvoke({
        "question": "北京烤鸭的制作工艺",
        "history": []
    })
    print(f"  答案长度: {len(response2.get('answer', ''))}")
    print(f"  Sources: {len(response2.get('sources', []))}")
    print(f"  Steps: {response2.get('steps', [])}")
    if response2.get('sources'):
        print(f"  Source示例: {response2['sources'][0]}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fallback())
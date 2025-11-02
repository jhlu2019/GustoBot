#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试KB workflow返回的完整响应"""

import asyncio
import sys
sys.path.append('F:/pythonproject/GustoBot')

from gustobot.application.agents.kg_sub_graph.agentic_rag_agents.workflows.multi_agent.multi_tool import (
    create_kb_multi_tool_workflow
)
from gustobot.infrastructure.knowledge import KnowledgeService
from gustobot.application.agents.models import openai_llm
from gustobot.config import settings

async def debug_workflow():
    """调试workflow返回的完整数据"""

    print("=" * 60)
    print("调试KB Workflow响应")
    print("=" * 60)

    # 初始化
    llm = openai_llm()
    knowledge_service = KnowledgeService()

    # 创建workflow
    workflow = create_kb_multi_tool_workflow(
        llm=llm,
        knowledge_service=knowledge_service,
        top_k=3,
        similarity_threshold=0.3,
        allow_external=False,
        external_search_url=None,
    )

    # 执行查询
    question = "东坡肉的历史是什么"

    response = await workflow.ainvoke({
        "question": question,
        "history": []
    })

    print(f"\n问题: {question}")
    print(f"\n响应包含的键: {list(response.keys())}")

    # 检查各个字段
    answer = response.get("answer", "")
    sources = response.get("sources", [])
    steps = response.get("steps", [])

    print(f"\nAnswer长度: {len(answer)} 字符")
    print(f"Sources数量: {len(sources)}")
    print(f"Steps: {steps}")

    if sources:
        print(f"\nSources内容:")
        for i, src in enumerate(sources, 1):
            print(f"  {i}. {src}")
    else:
        print("\n[!] Sources为空")

    print(f"\nAnswer预览: {answer[:200]}...")

    # 检查是否有其他隐藏的字段
    for key in response.keys():
        if key not in ["answer", "sources", "steps"]:
            print(f"\n其他字段 {key}:")
            print(f"  值: {response[key]}")

if __name__ == "__main__":
    asyncio.run(debug_workflow())
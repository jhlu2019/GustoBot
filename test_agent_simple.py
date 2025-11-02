#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单测试 agent 文件"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_prompts():
    """测试 prompts 文件"""
    print("=== Testing lg_prompts.py ===")

    try:
        from gustobot.application.agents.lg_prompts import (
            ROUTER_SYSTEM_PROMPT,
            GENERAL_QUERY_SYSTEM_PROMPT,
            GET_ADDITIONAL_SYSTEM_PROMPT,
            RAGSEARCH_SYSTEM_PROMPT,
            GUARDRAILS_SYSTEM_PROMPT,
            IMAGE_GENERATION_ENHANCE_PROMPT,
            IMAGE_GENERATION_SUCCESS_PROMPT,
            CHECK_HALLUCINATIONS
        )

        # 检查 router prompt
        if ROUTER_SYSTEM_PROMPT:
            print(f"[OK] Router prompt defined (length: {len(ROUTER_SYSTEM_PROMPT)})")

            # 检查路由类型
            routes = ["kb-query", "general-query", "graphrag-query", "text2sql-query", "additional-query"]
            for route in routes:
                if route in ROUTER_SYSTEM_PROMPT:
                    print(f"  [OK] Contains route: {route}")
                else:
                    print(f"  [FAIL] Missing route: {route}")
        else:
            print("[FAIL] Router prompt not defined")

        # 检查其他 prompts
        prompts = {
            "General Query": GENERAL_QUERY_SYSTEM_PROMPT,
            "Additional Query": GET_ADDITIONAL_SYSTEM_PROMPT,
            "RAG Search": RAGSEARCH_SYSTEM_PROMPT,
            "Guardrails": GUARDRAILS_SYSTEM_PROMPT,
            "Image Enhance": IMAGE_GENERATION_ENHANCE_PROMPT,
            "Image Success": IMAGE_GENERATION_SUCCESS_PROMPT,
            "Hallucination Check": CHECK_HALLUCINATIONS
        }

        for name, prompt in prompts.items():
            if prompt:
                print(f"[OK] {name} prompt defined (length: {len(prompt)})")
            else:
                print(f"[FAIL] {name} prompt not defined")

        # 检查模板占位符
        if "{logic}" in GENERAL_QUERY_SYSTEM_PROMPT:
            print("[OK] General query prompt has {logic} placeholder")
        if "{context}" in RAGSEARCH_SYSTEM_PROMPT:
            print("[OK] RAG search prompt has {context} placeholder")
        if "{user_query}" in IMAGE_GENERATION_ENHANCE_PROMPT:
            print("[OK] Image enhance prompt has {user_query} placeholder")

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")

    print()


def test_builder():
    """测试 builder 文件"""
    print("=== Testing lg_builder.py ===")

    try:
        from gustobot.application.agents.lg_builder import (
            build_supervisor_graph,
            analyze_and_route_query,
            respond_to_general_query,
            safety_guardrails
        )

        # 测试导入
        print("[OK] All functions imported successfully")

        # 测试图构建
        try:
            graph = build_supervisor_graph()
            if graph:
                print("[OK] Supervisor graph builds successfully")
            else:
                print("[FAIL] Graph build returned None")
        except Exception as e:
            print(f"[FAIL] Graph build failed: {e}")

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")

    print()


def test_states():
    """测试 states 文件"""
    print("=== Testing lg_states.py ===")

    try:
        from gustobot.application.agents.lg_states import (
            AgentState,
            InputState,
            Router,
            RouteResult
        )

        print("[OK] All state classes imported")

        # 测试创建状态对象
        try:
            router = Router(
                decision="kb-query",
                confidence=0.9,
                reasoning="Test reasoning"
            )
            print(f"[OK] Router object created: {router.decision}")

            route_result = RouteResult(
                route="kb-query",
                confidence=0.9,
                next_node="kb_query_node",
                metadata={"test": True}
            )
            print(f"[OK] RouteResult object created: {route_result.route}")

        except Exception as e:
            print(f"[FAIL] State object creation failed: {e}")

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")

    print()


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Testing Agent Files (Simplified)")
    print("="*60 + "\n")

    test_prompts()
    test_builder()
    test_states()

    print("="*60)
    print("Agent file testing completed!")
    print("="*60)


if __name__ == "__main__":
    main()
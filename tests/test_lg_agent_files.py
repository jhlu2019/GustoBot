#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test lg_builder.py and lg_prompts.py functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gustobot.application.agents.lg_prompts import (
    ROUTER_SYSTEM_PROMPT,
    GENERAL_QUERY_SYSTEM_PROMPT,
    GET_ADDITIONAL_SYSTEM_PROMPT,
    RAGSEARCH_SYSTEM_PROMPT,
    GUARDRAILS_SYSTEM_PROMPT,
    IMAGE_GENERATION_ENHANCE_PROMPT
)
from gustobot.application.agents.lg_builder import (
    build_supervisor_graph,
    analyze_and_route_query,
    respond_to_general_query,
    safety_guardrails
)
import asyncio


def test_prompts():
    """Test that all prompts are properly defined"""
    print("=== Testing Prompts ===")

    # Check router prompt
    assert ROUTER_SYSTEM_PROMPT, "ROUTER_SYSTEM_PROMPT not defined"
    print(f"✓ Router prompt defined (length: {len(ROUTER_SYSTEM_PROMPT)} chars)")

    # Check key content in router prompt
    assert "kb-query" in ROUTER_SYSTEM_PROMPT, "Router prompt missing kb-query"
    assert "general-query" in ROUTER_SYSTEM_PROMPT, "Router prompt missing general-query"
    assert "graphrag-query" in ROUTER_SYSTEM_PROMPT, "Router prompt missing graphrag-query"
    print("✓ Router prompt contains required route types")

    # Check other prompts
    assert GENERAL_QUERY_SYSTEM_PROMPT, "GENERAL_QUERY_SYSTEM_PROMPT not defined"
    assert GET_ADDITIONAL_SYSTEM_PROMPT, "GET_ADDITIONAL_SYSTEM_PROMPT not defined"
    assert RAGSEARCH_SYSTEM_PROMPT, "RAGSEARCH_SYSTEM_PROMPT not defined"
    assert GUARDRAILS_SYSTEM_PROMPT, "GUARDRAILS_SYSTEM_PROMPT not defined"
    print("✓ All prompts defined")

    # Check image generation prompt
    assert IMAGE_GENERATION_ENHANCE_PROMPT, "IMAGE_GENERATION_ENHANCE_PROMPT not defined"
    assert "宫保鸡丁" in IMAGE_GENERATION_ENHANCE_PROMPT, "Image prompt missing example"
    print("✓ Image generation prompt defined with example")

    print()


def test_builder_functions():
    """Test that builder functions are importable"""
    print("=== Testing Builder Functions ===")

    # Test imports
    assert build_supervisor_graph, "build_supervisor_graph not imported"
    assert analyze_and_route_query, "analyze_and_route_query not imported"
    assert respond_to_general_query, "respond_to_general_query not imported"
    assert safety_guardrails, "safety_guardrails not imported"
    print("✓ All builder functions imported successfully")

    # Test graph building
    try:
        graph = build_supervisor_graph()
        assert graph is not None, "Graph build returned None"
        print("✓ Supervisor graph builds successfully")
    except Exception as e:
        print(f"✗ Graph build failed: {e}")
        return False

    print()
    return True


async def test_routing_logic():
    """Test routing logic with sample queries"""
    print("=== Testing Routing Logic ===")

    # Test state format
    test_state = {
        "user_query": "红烧肉怎么做？",
        "session_id": "test_session",
        "conversation_history": []
    }

    print("Test queries and expected routes:")
    test_cases = [
        ("红烧肉怎么做", "graphrag-query or kb-query"),
        ("红烧肉的历史", "kb-query"),
        ("你好", "general-query"),
        ("有多少道菜", "text2sql-query"),
        ("我想做菜", "additional-query")
    ]

    for query, expected in test_cases:
        print(f"  Query: {query}")
        print(f"  Expected: {expected}")

    print("\nNote: Actual routing requires LLM calls and full environment setup")
    print()


def test_prompt_templates():
    """Test prompt template formatting"""
    print("=== Testing Prompt Templates ===")

    # Test template placeholders
    assert "{logic}" in GENERAL_QUERY_SYSTEM_PROMPT, "Missing {logic} placeholder"
    assert "{logic}" in GET_ADDITIONAL_SYSTEM_PROMPT, "Missing {logic} placeholder"
    assert "{context}" in RAGSEARCH_SYSTEM_PROMPT, "Missing {context} placeholder"
    print("✓ All templates have required placeholders")

    # Test image prompt template
    assert "{user_query}" in IMAGE_GENERATION_ENHANCE_PROMPT, "Missing {user_query} placeholder"
    print("✓ Image generation prompt has placeholder")

    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Testing lg_prompts.py and lg_builder.py")
    print("=" * 60 + "\n")

    # Test prompts
    test_prompts()

    # Test builder functions
    if not test_builder_functions():
        print("Builder function tests failed!")
        return

    # Test routing logic (async)
    asyncio.run(test_routing_logic())

    # Test prompt templates
    test_prompt_templates()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
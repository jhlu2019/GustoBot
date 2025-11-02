#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test lg_prompts.py and lg_builder.py functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gustobot.application.agents import lg_prompts, lg_builder

def test_lg_prompts():
    """Test lg_prompts module"""
    print("=== Testing lg_prompts.py ===")

    # Check if all required prompts exist
    prompts = [
        'ANALYZE_AND_ROUTE_QUERY_PROMPT',
        'SAFETY_GUARDRAILS_PROMPT',
        'RESPOND_TO_GENERAL_QUERY_PROMPT',
        'CREATE_KB_QUERY_PROMPT',
        'CREATE_RESEARCH_PLAN_PROMPT',
        'ADDITIONAL_QUERY_FALLBACK_PROMPT',
        'TEXT2SQL_QUERY_PROMPT',
        'SAFETY_REFUSAL_PROMPT'
    ]

    for prompt_name in prompts:
        if hasattr(lg_prompts, prompt_name):
            prompt = getattr(lg_prompts, prompt_name)
            print(f"  ✓ {prompt_name}: Exists ({len(prompt)} chars)")
        else:
            print(f"  ✗ {prompt_name}: Missing")

    # Test prompt formatting
    try:
        formatted = lg_prompts.ANALYZE_AND_ROUTE_QUERY_PROMPT.format(
            question="红烧肉怎么做？",
            history="[]"
        )
        print(f"  ✓ Prompt formatting works")
    except Exception as e:
        print(f"  ✗ Prompt formatting failed: {e}")

    print()

def test_lg_builder():
    """Test lg_builder module"""
    print("=== Testing lg_builder.py ===")

    # Test imports
    try:
        from gustobot.application.agents.lg_builder import (
            analyze_and_route_query,
            safety_guardrails,
            respond_to_general_query,
            create_kb_query,
            create_research_plan,
            additional_query_fallback,
            text2sql_query,
            safety_refusal
        )
        print("  ✓ All agent functions imported successfully")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return

    # Test function signatures
    functions = [
        (analyze_and_route_query, "analyze_and_route_query"),
        (safety_guardrails, "safety_guardrails"),
        (respond_to_general_query, "respond_to_general_query"),
        (create_kb_query, "create_kb_query"),
        (create_research_plan, "create_research_plan"),
        (additional_query_fallback, "additional_query_fallback"),
        (text2sql_query, "text2sql_query"),
        (safety_refusal, "safety_refusal")
    ]

    for func, name in functions:
        try:
            # Check if function is callable
            if callable(func):
                print(f"  ✓ {name}: Callable")
            else:
                print(f"  ✗ {name}: Not callable")
        except Exception as e:
            print(f"  ✗ {name}: Error - {e}")

    # Test state classes
    try:
        from gustobot.application.agents.lg_states import InputState, AgentState
        print(f"  ✓ InputState: Defined")
        print(f"  ✓ AgentState: Defined")
    except ImportError as e:
        print(f"  ✗ State import failed: {e}")

    print()

def test_prompt_content():
    """Test key prompt content"""
    print("=== Testing Prompt Content ===")

    # Check routing prompt has expected content
    routing_prompt = lg_prompts.ANALYZE_AND_ROUTE_QUERY_PROMPT
    expected_routes = ["kb-query", "general-query", "additional-query", "text2sql-query", "graphrag-query", "reject"]

    for route in expected_routes:
        if route in routing_prompt:
            print(f"  ✓ Route '{route}' found in routing prompt")
        else:
            print(f"  ✗ Route '{route}' missing from routing prompt")

    # Check safety prompt
    if "unsafe" in lg_prompts.SAFETY_GUARDRAILS_PROMPT.lower():
        print(f"  ✓ Safety prompt contains safety guidelines")
    else:
        print(f"  ✗ Safety prompt may be incomplete")

    print()

def main():
    print("GustoBot Agent Files Testing")
    print("=" * 50)
    print()

    test_lg_prompts()
    test_lg_builder()
    test_prompt_content()

    print("=" * 50)
    print("✓ All agent files tests completed")

if __name__ == "__main__":
    main()
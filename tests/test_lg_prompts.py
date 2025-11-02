#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test lg_prompts.py functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def test_router_prompt():
    """Test router prompt content"""
    print("=== Testing Router Prompt ===")

    # Check prompt exists
    assert ROUTER_SYSTEM_PROMPT, "ROUTER_SYSTEM_PROMPT not defined"
    print(f"✓ Router prompt defined (length: {len(ROUTER_SYSTEM_PROMPT)} chars)")

    # Check route types
    route_types = ["kb-query", "general-query", "graphrag-query", "text2sql-query", "additional-query"]
    for route in route_types:
        assert route in ROUTER_SYSTEM_PROMPT, f"Router prompt missing {route}"
    print(f"✓ Router prompt contains all route types: {', '.join(route_types)}")

    # Check key instructions
    key_phrases = [
        "菜谱领域的智能客服路由器",
        "历史文化",
        "做法步骤",
        "统计查询",
        "有多少"
    ]
    for phrase in key_phrases:
        assert phrase in ROUTER_SYSTEM_PROMPT, f"Router prompt missing key phrase: {phrase}"
    print("✓ Router prompt contains key routing instructions")

    print()


def test_general_query_prompt():
    """Test general query prompt"""
    print("=== Testing General Query Prompt ===")

    assert GENERAL_QUERY_SYSTEM_PROMPT, "GENERAL_QUERY_SYSTEM_PROMPT not defined"
    print(f"✓ General query prompt defined (length: {len(GENERAL_QUERY_SYSTEM_PROMPT)} chars)")

    # Check key phrases
    key_phrases = ["菜谱领域", "智能助手", "亲～", "顾客您好～", "感谢您的咨询"]
    for phrase in key_phrases:
        assert phrase in GENERAL_QUERY_SYSTEM_PROMPT, f"Missing phrase: {phrase}"
    print("✓ Contains required greeting and response patterns")

    # Check template placeholder
    assert "{logic}" in GENERAL_QUERY_SYSTEM_PROMPT, "Missing {logic} placeholder"
    print("✓ Has template placeholder")

    print()


def test_additional_query_prompt():
    """Test additional info query prompt"""
    print("=== Testing Additional Query Prompt ===")

    assert GET_ADDITIONAL_SYSTEM_PROMPT, "GET_ADDITIONAL_SYSTEM_PROMPT not defined"
    print(f"✓ Additional query prompt defined (length: {len(GET_ADDITIONAL_SYSTEM_PROMPT)} chars)")

    # Check key phrases
    key_phrases = ["厨友", "补充额外信息", "一次只问一个问题"]
    for phrase in key_phrases:
        assert phrase in GET_ADDITIONAL_SYSTEM_PROMPT, f"Missing phrase: {phrase}"
    print("✓ Contains proper instructions for asking follow-up questions")

    print()


def test_ragsearch_prompt():
    """Test RAG search prompt"""
    print("=== Testing RAG Search Prompt ===")

    assert RAGSEARCH_SYSTEM_PROMPT, "RAGSEARCH_SYSTEM_PROMPT not defined"
    print(f"✓ RAG search prompt defined (length: {len(RAGSEARCH_SYSTEM_PROMPT)} chars)")

    # Check key phrases
    key_phrases = ["专业的菜谱助手", "[${number}]", "不要编造答案"]
    for phrase in key_phrases:
        assert phrase in RAGSEARCH_SYSTEM_PROMPT, f"Missing phrase: {phrase}"
    print("✓ Contains proper RAG instructions")

    # Check template placeholder
    assert "{context}" in RAGSEARCH_SYSTEM_PROMPT, "Missing {context} placeholder"
    print("✓ Has context placeholder")

    print()


def test_guardrails_prompt():
    """Test guardrails prompt"""
    print("=== Testing Guardrails Prompt ===")

    assert GUARDRAILS_SYSTEM_PROMPT, "GUARDRAILS_SYSTEM_PROMPT not defined"
    print(f"✓ Guardrails prompt defined (length: {len(GUARDRAILS_SYSTEM_PROMPT)} chars)")

    # Check key instructions
    assert "continue" in GUARDRAILS_SYSTEM_PROMPT, "Missing 'continue' instruction"
    assert "end" in GUARDRAILS_SYSTEM_PROMPT, "Missing 'end' instruction"
    assert "菜谱管理系统相关" in GUARDRAILS_SYSTEM_PROMPT, "Missing scope definition"
    print("✓ Contains proper guardrails instructions")

    print()


def test_image_prompts():
    """Test image generation prompts"""
    print("=== Testing Image Generation Prompts ===")

    # Test enhance prompt
    assert IMAGE_GENERATION_ENHANCE_PROMPT, "IMAGE_GENERATION_ENHANCE_PROMPT not defined"
    print(f"✓ Image enhance prompt defined (length: {len(IMAGE_GENERATION_ENHANCE_PROMPT)} chars)")

    # Check example
    assert "宫保鸡丁" in IMAGE_GENERATION_ENHANCE_PROMPT, "Missing example"
    assert "商业美食摄影" in IMAGE_GENERATION_ENHANCE_PROMPT, "Missing style instruction"
    print("✓ Contains example and style instructions")

    # Check placeholder
    assert "{user_query}" in IMAGE_GENERATION_ENHANCE_PROMPT, "Missing {user_query} placeholder"
    print("✓ Has user query placeholder")

    # Test success prompt
    assert IMAGE_GENERATION_SUCCESS_PROMPT, "IMAGE_GENERATION_SUCCESS_PROMPT not defined"
    assert "{dish_name}" in IMAGE_GENERATION_SUCCESS_PROMPT, "Missing {dish_name} placeholder"
    print("✓ Success prompt defined with placeholder")

    print()


def test_hallucination_check():
    """Test hallucination check prompt"""
    print("=== Testing Hallucination Check Prompt ===")

    assert CHECK_HALLUCINATIONS, "CHECK_HALLUCINATIONS not defined"
    print(f"✓ Hallucination check prompt defined (length: {len(CHECK_HALLUCINATIONS)} chars)")

    # Check scoring instructions
    assert "1或0的评分" in CHECK_HALLUCINATIONS, "Missing scoring instruction"
    assert "{documents}" in CHECK_HALLUCINATIONS, "Missing documents placeholder"
    assert "{generation}" in CHECK_HALLUCINATIONS, "Missing generation placeholder"
    print("✓ Contains proper scoring instructions with placeholders")

    print()


def test_prompt_consistency():
    """Test prompt consistency and quality"""
    print("=== Testing Prompt Consistency ===")

    all_prompts = {
        "Router": ROUTER_SYSTEM_PROMPT,
        "General Query": GENERAL_QUERY_SYSTEM_PROMPT,
        "Additional Query": GET_ADDITIONAL_SYSTEM_PROMPT,
        "RAG Search": RAGSEARCH_SYSTEM_PROMPT,
        "Guardrails": GUARDRAILS_SYSTEM_PROMPT,
        "Image Enhance": IMAGE_GENERATION_ENHANCE_PROMPT,
        "Image Success": IMAGE_GENERATION_SUCCESS_PROMPT,
        "Hallucination Check": CHECK_HALLUCINATIONS
    }

    # Check all prompts are non-empty
    for name, prompt in all_prompts.items():
        assert len(prompt.strip()) > 0, f"Prompt {name} is empty"
    print("✓ All prompts are non-empty")

    # Check prompts are reasonably detailed
    for name, prompt in all_prompts.items():
        assert len(prompt) > 100, f"Prompt {name} too short ({len(prompt)} chars)"
    print("✓ All prompts have sufficient detail")

    # Check for consistent formatting
    template_counts = {}
    for name, prompt in all_prompts.items():
        placeholders = prompt.count("{")
        if placeholders > 0:
            template_counts[name] = placeholders

    print(f"✓ Template placeholders found: {template_counts}")

    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Testing lg_prompts.py")
    print("=" * 60 + "\n")

    test_router_prompt()
    test_general_query_prompt()
    test_additional_query_prompt()
    test_ragsearch_prompt()
    test_guardrails_prompt()
    test_image_prompts()
    test_hallucination_check()
    test_prompt_consistency()

    print("=" * 60)
    print("✅ All lg_prompts.py tests passed successfully!")
    print("=" * 60)

    # Print summary
    print("\nPrompt Summary:")
    print(f"  - Router: {len(ROUTER_SYSTEM_PROMPT)} chars")
    print(f"  - General Query: {len(GENERAL_QUERY_SYSTEM_PROMPT)} chars")
    print(f"  - Additional Query: {len(GET_ADDITIONAL_SYSTEM_PROMPT)} chars")
    print(f"  - RAG Search: {len(RAGSEARCH_SYSTEM_PROMPT)} chars")
    print(f"  - Guardrails: {len(GUARDRAILS_SYSTEM_PROMPT)} chars")
    print(f"  - Image Enhance: {len(IMAGE_GENERATION_ENHANCE_PROMPT)} chars")
    print(f"  - Image Success: {len(IMAGE_GENERATION_SUCCESS_PROMPT)} chars")
    print(f"  - Hallucination Check: {len(CHECK_HALLUCINATIONS)} chars")


if __name__ == "__main__":
    main()
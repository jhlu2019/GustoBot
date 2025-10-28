#!/usr/bin/env python3
"""
GustoBot Multi-Agent System Comprehensive Test
测试所有Agent路由和功能
"""
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

import asyncio
from app.agents.lg_states import InputState
from app.agents.utils import new_uuid
from app.agents.lg_builder import graph
from langchain_core.messages import HumanMessage
import json
from datetime import datetime


class AgentTester:
    """Agent系统测试类"""

    def __init__(self):
        self.thread = {"configurable": {"thread_id": new_uuid()}}
        self.results = []

    async def test_query(self, query: str, expected_type: str, description: str):
        """测试单个查询"""
        print(f"\n{'='*80}")
        print(f"🧪 测试: {description}")
        print(f"{'='*80}")
        print(f"📝 查询: {query}")
        print(f"🎯 期望路由: {expected_type}")
        print(f"-"*80)

        start_time = datetime.now()

        try:
            # Create new thread for each test to avoid state pollution
            thread = {"configurable": {"thread_id": new_uuid()}}
            inputState = InputState(messages=[HumanMessage(content=query)])

            response_content = []
            router_type = None
            router_logic = None

            # Stream the response
            async for chunk, metadata in graph.astream(
                input=inputState,
                stream_mode="messages",
                config=thread
            ):
                if chunk.content and "research_plan" not in metadata.get("tags", []):
                    response_content.append(chunk.content)
                    print(chunk.content, end="", flush=True)

            # Get final state to check routing
            state = graph.get_state(thread)
            if state and len(state) > 0:
                final_state = state[0]
                if hasattr(final_state, 'values') and 'router' in final_state.values:
                    router_info = final_state.values['router']
                    router_type = router_info.get('type')
                    router_logic = router_info.get('logic')

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            full_response = "".join(response_content)

            print(f"\n{'-'*80}")
            print(f"✅ 完成 (耗时: {duration:.2f}s)")
            print(f"🔀 实际路由: {router_type}")
            print(f"💭 路由逻辑: {router_logic}")

            result = {
                "description": description,
                "query": query,
                "expected_type": expected_type,
                "actual_type": router_type,
                "router_logic": router_logic,
                "response": full_response[:200] + "..." if len(full_response) > 200 else full_response,
                "duration_seconds": duration,
                "success": router_type == expected_type,
                "timestamp": start_time.isoformat()
            }

            self.results.append(result)

            if router_type == expected_type:
                print(f"✅ 路由正确")
            else:
                print(f"⚠️  路由不匹配 (期望: {expected_type}, 实际: {router_type})")

            return result

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "description": description,
                "query": query,
                "expected_type": expected_type,
                "actual_type": "ERROR",
                "error": str(e),
                "duration_seconds": duration,
                "success": False,
                "timestamp": start_time.isoformat()
            }

            self.results.append(result)
            return result

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 GustoBot Multi-Agent System Comprehensive Test")
        print("="*80 + "\n")

        test_cases = [
            # 1. General Query (闲聊)
            {
                "query": "你好，今天天气不错",
                "expected_type": "general-query",
                "description": "通用闲聊 - 问候语"
            },
            {
                "query": "你是谁？",
                "expected_type": "general-query",
                "description": "通用闲聊 - 自我介绍"
            },
            {
                "query": "讲个笑话",
                "expected_type": "general-query",
                "description": "通用闲聊 - 娱乐请求"
            },

            # 2. Knowledge Base Query (知识库查询)
            {
                "query": "红烧肉怎么做？",
                "expected_type": "kb-query",
                "description": "知识库查询 - 菜谱做法"
            },
            {
                "query": "五花肉可以做什么菜？",
                "expected_type": "kb-query",
                "description": "知识库查询 - 食材应用"
            },
            {
                "query": "川菜有哪些代表菜？",
                "expected_type": "kb-query",
                "description": "知识库查询 - 菜系分类"
            },
            {
                "query": "炒菜时如何掌握火候？",
                "expected_type": "kb-query",
                "description": "知识库查询 - 烹饪技巧"
            },

            # 3. GraphRAG Query (知识图谱查询)
            {
                "query": "香肠炒菜干需要什么食材？",
                "expected_type": "graphrag-query",
                "description": "图谱查询 - 食材关系"
            },
            {
                "query": "红烧肉的主要食材和辅料是什么？",
                "expected_type": "graphrag-query",
                "description": "图谱查询 - 食材分类"
            },
            {
                "query": "麻婆豆腐属于什么菜系？用什么烹饪方法？",
                "expected_type": "graphrag-query",
                "description": "图谱查询 - 多维度关系"
            },
            {
                "query": "宫保鸡丁有什么健康益处？",
                "expected_type": "graphrag-query",
                "description": "图谱查询 - 健康关系"
            },

            # 4. Additional Info Query (追问)
            # Note: 这类查询需要有上下文，暂时跳过独立测试

            # 5. Text2SQL Query (结构化查询) - if supported
            {
                "query": "统计一下川菜有多少道？",
                "expected_type": "text2sql-query",
                "description": "SQL查询 - 统计类"
            },
            {
                "query": "查询所有包含鸡肉的菜谱",
                "expected_type": "text2sql-query",
                "description": "SQL查询 - 检索类"
            },

            # 6. Edge Cases (边界情况)
            {
                "query": "红烧肉的历史渊源是什么？",
                "expected_type": "kb-query",  # Could be kb or graphrag
                "description": "边界情况 - 历史文化查询"
            },
            {
                "query": "如何判断红烧肉是否炖好了？",
                "expected_type": "kb-query",
                "description": "边界情况 - 经验判断类"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}]")
            await self.test_query(
                query=test_case["query"],
                expected_type=test_case["expected_type"],
                description=test_case["description"]
            )

            # Sleep between tests to avoid overwhelming the system
            await asyncio.sleep(1)

        # Print summary
        self.print_summary()

        # Save results
        self.save_results()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)

        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful

        print(f"总测试数: {total}")
        print(f"✅ 成功: {successful} ({successful/total*100:.1f}%)")
        print(f"❌ 失败: {failed} ({failed/total*100:.1f}%)")

        # Group by router type
        print(f"\n{'='*80}")
        print("按路由类型分组:")
        print(f"{'='*80}")

        type_stats = {}
        for result in self.results:
            actual_type = result.get("actual_type", "UNKNOWN")
            if actual_type not in type_stats:
                type_stats[actual_type] = {"count": 0, "success": 0}
            type_stats[actual_type]["count"] += 1
            if result["success"]:
                type_stats[actual_type]["success"] += 1

        for router_type, stats in sorted(type_stats.items()):
            success_rate = stats["success"] / stats["count"] * 100 if stats["count"] > 0 else 0
            print(f"  {router_type:20s}: {stats['count']:2d} 次 ({stats['success']:2d} 成功, {success_rate:.0f}%)")

        # Failed cases
        if failed > 0:
            print(f"\n{'='*80}")
            print("失败案例:")
            print(f"{'='*80}")
            for result in self.results:
                if not result["success"]:
                    print(f"  ❌ {result['description']}")
                    print(f"     查询: {result['query']}")
                    print(f"     期望: {result['expected_type']}, 实际: {result.get('actual_type', 'N/A')}")
                    if 'error' in result:
                        print(f"     错误: {result['error']}")
                    print()

        # Performance stats
        print(f"{'='*80}")
        print("性能统计:")
        print(f"{'='*80}")

        durations = [r["duration_seconds"] for r in self.results if "duration_seconds" in r]
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)

            print(f"  平均响应时间: {avg_duration:.2f}s")
            print(f"  最快响应: {min_duration:.2f}s")
            print(f"  最慢响应: {max_duration:.2f}s")

    def save_results(self):
        """保存测试结果到JSON文件"""
        output_file = Path(__file__).parent / "agent_test_results.json"

        report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "successful_tests": sum(1 for r in self.results if r["success"]),
                "failed_tests": sum(1 for r in self.results if not r["success"]),
            },
            "test_results": self.results
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 测试结果已保存到: {output_file}")


async def main():
    """主函数"""
    tester = AgentTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
GraphRAG Multi-Tool测试
测试graphrag-query内的各个工具分支
"""
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import asyncio
from gustobot.application.agents.lg_states import InputState
from gustobot.application.agents.utils import new_uuid
from gustobot.application.agents.lg_builder import graph
from langchain_core.messages import HumanMessage
from datetime import datetime

class GraphRAGToolTester:
    """GraphRAG工具测试类"""

    def __init__(self):
        self.results = []

    async def test_query(self, query: str, expected_tool: str, description: str):
        """测试单个查询并观察工具选择"""
        print(f"\n{'='*80}")
        print(f"🔧 测试: {description}")
        print(f"{'='*80}")
        print(f"📝 查询: {query}")
        print(f"🎯 期望工具: {expected_tool}")
        print(f"-"*80)

        start_time = datetime.now()
        thread = {"configurable": {"thread_id": new_uuid()}}
        inputState = InputState(messages=[HumanMessage(content=query)])

        try:
            response_parts = []
            print("🔄 执行中...")

            async for chunk, metadata in graph.astream(
                input=inputState,
                stream_mode="messages",
                config=thread
            ):
                if chunk.content:
                    response_parts.append(chunk.content)
                    # 只打印非research_plan的内容
                    if "research_plan" not in metadata.get("tags", []):
                        print(chunk.content, end="", flush=True)

            full_response = "".join(response_parts)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 检查路由
            state = graph.get_state(thread)
            router_type = "unknown"
            if state and len(state) > 0:
                try:
                    state_values = state[0].values() if callable(state[0].values) else state[0].values
                    router_info = state_values.get('router', {})
                    router_type = router_info.get('type', 'unknown')
                except:
                    pass

            print(f"\n{'-'*80}")
            print(f"⏱️  耗时: {duration:.2f}秒")
            print(f"🔀 路由类型: {router_type}")
            print(f"📊 响应长度: {len(full_response)}字符")

            result = {
                "description": description,
                "query": query,
                "expected_tool": expected_tool,
                "router_type": router_type,
                "response": full_response[:300] + "..." if len(full_response) > 300 else full_response,
                "response_length": len(full_response),
                "duration_seconds": duration,
                "success": router_type == "graphrag-query",
                "timestamp": start_time.isoformat()
            }

            self.results.append(result)

            if router_type == "graphrag-query":
                print(f"✅ 路由正确 (graphrag-query)")
            else:
                print(f"⚠️  路由到了: {router_type}")

            return result

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

            result = {
                "description": description,
                "query": query,
                "expected_tool": expected_tool,
                "error": str(e),
                "success": False
            }
            self.results.append(result)
            return result

    async def run_tests(self):
        """运行所有工具测试"""
        print("\n" + "="*80)
        print("🚀 GraphRAG Multi-Tool System Test")
        print("="*80 + "\n")

        test_cases = [
            # 1. 预定义Cypher工具 (predefined_cypher)
            {
                "query": "红烧肉怎么做？",
                "expected_tool": "predefined_cypher",
                "description": "预定义Cypher - 菜谱做法查询"
            },
            {
                "query": "香肠炒菜干需要多长时间？",
                "expected_tool": "predefined_cypher",
                "description": "预定义Cypher - 烹饪时间查询"
            },

            # 2. Neo4j Text2Cypher工具 (dynamic cypher generation)
            {
                "query": "香肠炒菜干需要什么食材？",
                "expected_tool": "text2cypher",
                "description": "Text2Cypher - 食材关系查询"
            },
            {
                "query": "麻婆豆腐的主料和辅料是什么？",
                "expected_tool": "text2cypher",
                "description": "Text2Cypher - 主辅料查询"
            },
            {
                "query": "宫保鸡丁用什么烹饪方法？",
                "expected_tool": "text2cypher",
                "description": "Text2Cypher - 烹饪方法查询"
            },
            {
                "query": "五花肉可以做什么菜？",
                "expected_tool": "text2cypher",
                "description": "Text2Cypher - 食材应用查询"
            },

            # 3. Custom Tools (graphrag_query_node)
            {
                "query": "红烧肉有什么健康益处？",
                "expected_tool": "custom_tools",
                "description": "Custom Tools - 健康益处查询"
            },
            {
                "query": "麻婆豆腐的营养成分是什么？",
                "expected_tool": "custom_tools",
                "description": "Custom Tools - 营养查询"
            },

            # 4. Text2SQL工具 (统计查询 - 如果支持)
            {
                "query": "统计川菜有多少道？",
                "expected_tool": "text2sql",
                "description": "Text2SQL - 统计类查询"
            },
            {
                "query": "查询所有包含鸡肉的菜谱数量",
                "expected_tool": "text2sql",
                "description": "Text2SQL - 条件统计查询"
            },

            # 5. 复杂查询（测试工具选择）
            {
                "query": "宫保鸡丁的完整烹饪步骤和所需食材",
                "expected_tool": "text2cypher",
                "description": "复杂查询 - 多维度信息"
            },
            {
                "query": "红烧肉的口味特点和适合的人群",
                "expected_tool": "text2cypher",
                "description": "复杂查询 - 口味与健康"
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}]")
            await self.test_query(
                query=test_case["query"],
                expected_tool=test_case["expected_tool"],
                description=test_case["description"]
            )

            # 短暂延迟避免过载
            await asyncio.sleep(1)

        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)

        total = len(self.results)
        success = sum(1 for r in self.results if r.get("success"))
        errors = sum(1 for r in self.results if "error" in r)

        print(f"总测试数: {total}")
        print(f"✅ 路由成功: {success} ({success/total*100:.1f}%)")
        print(f"❌ 错误: {errors} ({errors/total*100:.1f}%)")

        # 按工具类型分组
        print(f"\n{'='*80}")
        print("工具调用分布:")
        print(f"{'='*80}")

        tool_stats = {}
        for result in self.results:
            expected = result.get("expected_tool", "unknown")
            if expected not in tool_stats:
                tool_stats[expected] = {"count": 0, "success": 0}
            tool_stats[expected]["count"] += 1
            if result.get("success"):
                tool_stats[expected]["success"] += 1

        for tool, stats in sorted(tool_stats.items()):
            rate = stats["success"] / stats["count"] * 100 if stats["count"] > 0 else 0
            print(f"  {tool:20s}: {stats['count']:2d} 测试 ({stats['success']:2d} 成功, {rate:.0f}%)")

        # 性能统计
        if any("duration_seconds" in r for r in self.results):
            print(f"\n{'='*80}")
            print("性能统计:")
            print(f"{'='*80}")

            durations = [r["duration_seconds"] for r in self.results if "duration_seconds" in r]
            if durations:
                print(f"  平均响应: {sum(durations)/len(durations):.2f}秒")
                print(f"  最快: {min(durations):.2f}秒")
                print(f"  最慢: {max(durations):.2f}秒")

async def main():
    tester = GraphRAGToolTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())

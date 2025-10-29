#!/usr/bin/env python3
"""测试 Heuristic Router 关键词兜底机制"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.agents.lg_states import InputState
from app.agents.lg_builder import graph
from app.agents.utils import new_uuid
from langchain_core.messages import HumanMessage

async def test_query(query: str, expected_route: str, description: str):
    print(f'\n{"="*80}')
    print(f'🧪 {description}')
    print(f'{"="*80}')
    print(f'📝 查询: {query}')
    print(f'🎯 期望路由: {expected_route}')
    print(f'{"-"*80}')

    try:
        thread = {'configurable': {'thread_id': new_uuid()}}
        input_state = InputState(messages=[HumanMessage(content=query)])

        response_content = []
        router_type = None
        router_logic = None

        async for chunk, metadata in graph.astream(input_state, stream_mode='messages', config=thread):
            if chunk.content and 'research_plan' not in metadata.get('tags', []):
                response_content.append(chunk.content)
                # 只显示前 200 个字符
                if len(''.join(response_content)) < 200:
                    print(chunk.content, end='', flush=True)

        # 获取路由信息
        state = graph.get_state(thread)
        if state and len(state) > 0:
            final_state = state[0]
            if hasattr(final_state, 'values') and 'router' in final_state.values:
                router_info = final_state.values['router']
                router_type = router_info.get('type') if isinstance(router_info, dict) else None
                router_logic = router_info.get('logic') if isinstance(router_info, dict) else None

        print(f'\n{"-"*80}')
        print(f'🔀 实际路由: {router_type}')
        if router_logic:
            print(f'💭 路由逻辑: {router_logic}')

        # 检查是否有 heuristic override
        if router_logic and 'heuristic' in router_logic.lower():
            print(f'✨ 检测到关键词兜底机制！')

        success = router_type == expected_route
        if success:
            print(f'✅ 路由正确匹配')
        else:
            print(f'⚠️  路由不匹配 (期望: {expected_route}, 实际: {router_type})')

        return {'success': success, 'actual_route': router_type, 'logic': router_logic}

    except Exception as e:
        print(f'\n❌ 错误: {str(e)[:300]}')
        import traceback
        traceback.print_exc()
        return {'success': False, 'actual_route': 'ERROR', 'error': str(e)}

async def main():
    print(f'\n{"="*80}')
    print('🚀 Heuristic Router 关键词兜底机制测试')
    print(f'{"="*80}')
    print('关键词: 食材、做法、步骤、用什么、怎么做')
    print(f'{"="*80}')

    # 专门测试应该触发关键词兜底的查询
    test_cases = [
        {
            'query': '香肠炒菜干需要什么食材？',
            'expected': 'graphrag-query',
            'description': 'GraphRAG - 食材查询 (关键词: 食材) ⭐',
            'keywords': ['食材']
        },
        {
            'query': '红烧肉怎么做？',
            'expected': 'graphrag-query',
            'description': 'GraphRAG - 做法查询 (关键词: 怎么做) ⭐',
            'keywords': ['怎么做']
        },
        {
            'query': '麻婆豆腐的做法步骤是什么？',
            'expected': 'graphrag-query',
            'description': 'GraphRAG - 步骤查询 (关键词: 做法、步骤) ⭐',
            'keywords': ['做法', '步骤']
        },
        {
            'query': '宫保鸡丁用什么调料？',
            'expected': 'graphrag-query',
            'description': 'GraphRAG - 调料查询 (关键词: 用什么) ⭐',
            'keywords': ['用什么']
        },
        {
            'query': '你好',
            'expected': 'general-query',
            'description': 'General - 问候 (无关键词)',
            'keywords': []
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f'\n[测试 {i}/{len(test_cases)}]')
        print(f'期望触发关键词: {test_case["keywords"]}')

        result = await test_query(
            query=test_case['query'],
            expected_route=test_case['expected'],
            description=test_case['description']
        )

        result.update({
            'query': test_case['query'],
            'expected': test_case['expected'],
            'keywords': test_case['keywords']
        })
        results.append(result)

        await asyncio.sleep(1)

    # 打印总结
    print(f'\n{"="*80}')
    print('📊 测试总结')
    print(f'{"="*80}')

    total = len(results)
    passed = sum(1 for r in results if r['success'])

    print(f'总测试数: {total}')
    print(f'✅ 通过: {passed} ({passed/total*100:.1f}%)')
    print(f'❌ 失败: {total - passed}')

    # 关键词兜底统计
    print(f'\n{"-"*80}')
    print('关键词兜底机制触发情况:')
    print(f'{"-"*80}')

    heuristic_count = 0
    for result in results:
        if result.get('keywords') and result.get('logic'):
            logic = result.get('logic', '').lower()
            has_heuristic = 'heuristic' in logic or 'override' in logic or '关键词' in logic
            if has_heuristic:
                heuristic_count += 1
                print(f"✨ {result['query'][:30]}... → 兜底生效")
            elif result['keywords']:
                print(f"⚠️  {result['query'][:30]}... → 兜底未触发 (包含关键词: {result['keywords']})")

    print(f'\n关键词兜底触发次数: {heuristic_count}')

    # 路由分组统计
    print(f'\n{"-"*80}')
    print('路由分组统计:')
    print(f'{"-"*80}')

    route_stats = {}
    for result in results:
        route = result.get('actual_route', 'UNKNOWN')
        if route not in route_stats:
            route_stats[route] = 0
        route_stats[route] += 1

    for route, count in sorted(route_stats.items()):
        print(f'  {route:20s}: {count} 次')

    print(f'{"="*80}\n')

if __name__ == '__main__':
    asyncio.run(main())

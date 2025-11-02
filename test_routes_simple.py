import requests
import json

# API配置
BASE_URL = "http://localhost:8000"
CHAT_URL = f"{BASE_URL}/api/v1/chat"

# 测试用例
test_cases = [
    {
        "name": "General Query - 问候",
        "message": "你好",
        "expected_route": "general-query"
    },
    {
        "name": "KB Query - 历史典故",
        "message": "宫保鸡丁的历史典故是什么",
        "expected_route": "kb-query"
    },
    {
        "name": "KB Query - 营养价值",
        "message": "西兰花有什么营养价值",
        "expected_route": "kb-query"
    },
    {
        "name": "GraphRAG Query - 做法",
        "message": "红烧肉怎么做",
        "expected_route": "graphrag-query"
    },
    {
        "name": "GraphRAG Query - 食材",
        "message": "宫保鸡丁需要哪些食材",
        "expected_route": "graphrag-query"
    },
    {
        "name": "Text2SQL Query - 统计",
        "message": "数据库里有多少道菜",
        "expected_route": "text2sql-query"
    },
    {
        "name": "Additional Query - 模糊提问",
        "message": "我想做菜",
        "expected_route": "additional-query"
    },
    {
        "name": "Guardrails - 无关问题",
        "message": "今天天气怎么样",
        "expected_route": "general-query"
    }
]

def run_test():
    print("开始测试Agent路由...")
    print("="*60)

    results = []

    for test in test_cases:
        print(f"\n测试: {test['name']}")
        print(f"问题: {test['message']}")
        print(f"预期路由: {test['expected_route']}")

        payload = {
            "message": test['message'],
            "session_id": "test_session"
        }

        try:
            response = requests.post(CHAT_URL, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                metadata = data.get('metadata', {})
                actual_route = metadata.get('route', 'unknown')
                confidence = metadata.get('confidence', 0)

                print(f"实际路由: {actual_route}")
                print(f"置信度: {confidence:.2f}")

                # 检查是否匹配
                if actual_route == test['expected_route']:
                    print("结果: PASS ✓")
                    pass_test = True
                else:
                    print(f"结果: FAIL ✗ (预期: {test['expected_route']})")
                    pass_test = False

                results.append({
                    'test': test['name'],
                    'question': test['message'],
                    'expected': test['expected_route'],
                    'actual': actual_route,
                    'pass': pass_test,
                    'confidence': confidence
                })

            else:
                print(f"错误: HTTP {response.status_code}")
                print(response.text)
                results.append({
                    'test': test['name'],
                    'question': test['message'],
                    'expected': test['expected_route'],
                    'actual': 'ERROR',
                    'pass': False,
                    'confidence': 0
                })

        except Exception as e:
            print(f"异常: {str(e)}")
            results.append({
                'test': test['name'],
                'question': test['message'],
                'expected': test['expected_route'],
                'actual': 'EXCEPTION',
                'pass': False,
                'confidence': 0
            })

    # 汇总结果
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    total = len(results)
    passed = sum(1 for r in results if r['pass'])
    failed = total - passed

    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"成功率: {passed/total*100:.1f}%")

    # 显示失败的测试
    if failed > 0:
        print("\n失败的测试:")
        for r in results:
            if not r['pass']:
                print(f"  ✗ {r['test']}")
                print(f"    问题: {r['question']}")
                print(f"    预期: {r['expected']}, 实际: {r['actual']}")

    # 保存结果
    with open('route_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到: route_test_results.json")

if __name__ == "__main__":
    run_test()
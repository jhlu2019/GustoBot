"""
测试聊天 API 功能

验证统一聊天接口的各个路由类型
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# API 配置
API_BASE_URL = "http://localhost:8000/api/v1"

# 测试用例
TEST_CASES = [
    {
        "name": "问候对话",
        "message": "你好，我是新用户",
        "expected_route": "general-query"
    },
    {
        "name": "询问做法",
        "message": "红烧肉怎么做？",
        "expected_route": "graphrag-query"
    },
    {
        "name": "历史典故",
        "message": "宫保鸡丁有什么历史故事？",
        "expected_route": "kb-query"
    },
    {
        "name": "统计查询",
        "message": "数据库里有多少道菜？",
        "expected_route": "text2sql-query"
    },
    {
        "name": "模糊问题",
        "message": "我想学做菜",
        "expected_route": "additional-query"
    },
    {
        "name": "图片生成",
        "message": "生成一张麻婆豆腐的图片",
        "expected_route": "image-query"
    },
    {
        "name": "混合查询",
        "message": "川菜有哪些特点？统计一下数量",
        "expected_route": "text2sql-query"
    }
]

async def test_chat_api():
    """测试聊天 API"""
    print("🤖 测试 GustoBot 聊天 API")
    print("="*60)

    session_id = None

    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"\n测试 {i}/{len(TEST_CASES)}: {test_case['name']}")
            print(f"问题: {test_case['message']}")

            # 构建请求
            payload = {
                "message": test_case["message"],
                "session_id": session_id,
                "user_id": "test_user",
                "stream": False
            }

            try:
                # 发送请求
                async with session.post(
                    f"{API_BASE_URL}/chat/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # 更新会话ID
                        if data.get("session_id"):
                            session_id = data["session_id"]

                        # 显示结果
                        print(f"✅ 成功")
                        print(f"   路由: {data.get('route', 'unknown')}")
                        print(f"   逻辑: {data.get('route_logic', 'N/A')[:50]}...")
                        print(f"   回复: {data.get('message', 'N/A')[:100]}...")

                        # 检查路由
                        if data.get('route') == test_case['expected_route']:
                            print(f"   ✅ 路由正确")
                        else:
                            print(f"   ⚠️  预期路由: {test_case['expected_route']}")

                    else:
                        print(f"❌ 失败 - HTTP {response.status}")
                        error_text = await response.text()
                        print(f"   错误: {error_text[:100]}...")

            except Exception as e:
                print(f"❌ 错误: {str(e)}")

            # 添加延迟避免请求过快
            await asyncio.sleep(1)

    print("\n" + "="*60)
    print("测试完成！")

    # 获取聊天历史
    if session_id:
        print(f"\n获取会话历史 (Session ID: {session_id})")
        try:
            async with session.get(
                f"{API_BASE_URL}/chat/history/{session_id}"
            ) as response:
                if response.status == 200:
                    history = await response.json()
                    print(f"历史消息数: {len(history)}")
                    for msg in history[-3:]:  # 显示最后3条
                        sender = "用户" if msg['is_user'] else "助手"
                        print(f"  {sender}: {msg['message'][:50]}...")
        except Exception as e:
            print(f"获取历史失败: {e}")

async def test_stream_chat():
    """测试流式聊天"""
    print("\n🌊 测试流式聊天")
    print("="*40)

    payload = {
        "message": "请详细介绍川菜的特点",
        "session_id": None,
        "user_id": "stream_test_user"
    }

    url = f"{API_BASE_URL}/chat/chat/stream"
    params = {
        "message": payload["message"],
        "session_id": payload.get("session_id", ""),
        "user_id": payload["user_id"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    print("✅ 流式响应开始:")

                    full_message = ""
                    async for line in response.content:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = json.loads(line[6:])

                            if data['type'] == 'message':
                                full_message += data.get('content', '')
                                print(data.get('content', ''), end='', flush=True)

                            elif data['type'] == 'metadata':
                                if data.get('metadata', {}).get('route'):
                                    print(f"\n\n路由: {data['metadata']['route']}")

                            elif data['type'] == 'done':
                                print("\n\n✅ 流式响应完成")
                                break

                            elif data['type'] == 'error':
                                print(f"\n❌ 错误: {data.get('content', 'Unknown error')}")
                                break

                else:
                    print(f"❌ 失败 - HTTP {response.status}")

    except Exception as e:
        print(f"❌ 错误: {e}")

async def main():
    """主函数"""
    print("开始测试 GustoBot 聊天 API...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 测试常规聊天
    await test_chat_api()

    # 测试流式聊天
    await test_stream_chat()

    print("\n✨ 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
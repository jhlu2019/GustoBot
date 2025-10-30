#!/usr/bin/env python3
"""
简化的知识库初始化脚本
"""

import asyncio
import aiohttp
import json
from pathlib import Path

async def init_pgvector_from_excel():
    """使用ingest服务加载Excel数据到pgvector"""
    print("="*60)
    print("初始化pgvector数据（Excel）")
    print("="*60)

    excel_path = "/data/temp32/GustoBot/data/kb/历史菜谱源头.xlsx"

    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8100/api/v1/knowledge/ingest/excel"

        payload = {
            "excel_path": excel_path,
            "incremental": False
        }

        print(f"正在加载: {excel_path}")

        async with session.post(url, json=payload) as response:
            if response.status == 202:
                result = await response.json()
                print(f"✅ 成功提交Excel处理任务")
                print(f"   响应: {result}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ 提交失败: HTTP {response.status}")
                print(f"   错误: {error_text}")
                return False

async def add_sample_recipes():
    """添加一些示例菜谱数据"""
    print("\n" + "="*60)
    print("添加示例菜谱到向量库")
    print("="*60)

    # 准备示例数据
    recipes = [
        {
            "name": "麻婆豆腐",
            "description": "四川传统名菜，麻、辣、鲜、香、烫、整、嫩、酥。由豆腐、牛肉末、豆瓣酱和花椒等制成。",
            "category": "川菜",
            "history": "麻婆豆腐始创于清朝同治年间，由成都万福桥陈兴盛饭铺老板娘刘陈氏所创。因她脸上有麻点，人称陈麻婆。",
            "ingredients": ["豆腐", "牛肉末", "豆瓣酱", "花椒", "葱", "姜", "蒜"],
            "steps": ["豆腐切块焯水", "炒制牛肉末", "加入豆瓣酱炒出红油", "加入豆腐和调料"]
        },
        {
            "name": "宫保鸡丁",
            "description": "川菜传统名菜，鸡丁配花生米，红而不辣，辣而不猛，香辣味浓，肉质滑脆。",
            "category": "川菜",
            "history": "宫保鸡丁源于清朝，由山东巡抚丁宝桢发明。丁宝桢曾任宫保官职，故此菜被称为宫保鸡丁。",
            "ingredients": ["鸡胸肉", "花生米", "干辣椒", "花椒", "葱", "姜", "蒜"],
            "steps": ["鸡胸肉切丁腌制", "调制宫保汁", "炒制鸡丁", "加入花生和调料"]
        },
        {
            "name": "东坡肉",
            "description": "江南名菜，五花肉慢炖而成，色泽红亮，酥烂而形不碎，香糯而不腻口。",
            "category": "浙菜",
            "history": "东坡肉相传为北宋文学家苏东坡所创。苏东坡在杭州任职时，曾组织民工疏浚西湖，百姓感念其德，送来猪肉。苏东坡让家人将猪肉切成方块，烹制成红烧肉回赠给民工。",
            "ingredients": ["五花肉", "冰糖", "酱油", "料酒", "葱", "姜"],
            "steps": ["五花肉切块焯水", "炒糖色", "加入肉块翻炒", "慢炖收汁"]
        }
    ]

    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8100/api/v1/knowledge/recipes/batch"

        print(f"准备添加 {len(recipes)} 个菜谱")

        async with session.post(url, json=recipes) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 成功提交菜谱")
                print(f"   响应: {result}")
                return True
            else:
                error_text = await response.text()
                print(f"❌ 提交失败: HTTP {response.status}")
                print(f"   错误: {error_text}")
                return False

async def wait_and_check():
    """等待处理完成并检查统计"""
    print("\n等待处理完成...")
    await asyncio.sleep(5)

    print("\n" + "="*60)
    print("检查知识库统计")
    print("="*60)

    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8100/api/v1/knowledge/stats"

        async with session.get(url) as response:
            if response.status == 200:
                stats = await response.json()
                data = stats.get("data", {})
                print("知识库统计:")
                print(f"  集合名称: {data.get('name')}")
                print(f"  文档数量: {data.get('document_count')}")
                print(f"  向量维度: {data.get('dimension')}")
                print(f"  索引类型: {data.get('index_type')}")
                return data.get('document_count', 0)
            else:
                print(f"❌ 获取统计失败: HTTP {response.status}")
                return 0

async def test_search():
    """测试搜索功能"""
    print("\n" + "="*60)
    print("测试搜索功能")
    print("="*60)

    test_queries = [
        "麻婆豆腐历史",
        "宫保鸡丁来历",
        "东坡肉典故",
        "川菜特色"
    ]

    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n查询: {query}")
            print("-" * 40)

            url = "http://localhost:8100/api/v1/knowledge/search"
            payload = {
                "query": query,
                "top_k": 3,
                "threshold": 0.3
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    results = result.get("results", [])

                    if results:
                        print(f"✅ 找到 {len(results)} 条结果")
                        for i, res in enumerate(results[:2], 1):
                            content = res.get("content", "")[:150]
                            score = res.get("score", 0)
                            source = res.get("metadata", {}).get("source", "未知")
                            print(f"  {i}. [相似度: {score:.3f}] {content}... (来源: {source})")
                    else:
                        print("⚠️ 无结果")
                else:
                    print(f"❌ 搜索失败: HTTP {response.status}")

            await asyncio.sleep(0.5)

async def main():
    """主函数"""
    print("开始初始化知识库...\n")

    # 1. 初始化pgvector数据
    success1 = await init_pgvector_from_excel()

    # 2. 添加示例菜谱
    success2 = await add_sample_recipes()

    if success1 or success2:
        # 3. 等待并检查
        doc_count = await wait_and_check()

        if doc_count > 0:
            # 4. 测试搜索
            await test_search()
            print("\n✅ 初始化完成！知识库已有数据。")
        else:
            print("\n⚠️ 初始化完成，但知识库仍无数据。")
    else:
        print("\n❌ 初始化失败。")

if __name__ == "__main__":
    asyncio.run(main())
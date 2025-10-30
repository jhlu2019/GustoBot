#!/usr/bin/env python3
"""
初始化知识库数据
1. 加载Excel数据到PostgreSQL pgvector
2. 加载文本数据到Milvus向量库
"""

import asyncio
import json
import aiohttp
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# 配置
INGEST_URL = "http://localhost:8000"
EXCEL_FILE = "data/kb/历史菜谱源头.xlsx"
TEXT_FILE = "data/kb/data.txt"

async def load_excel_to_pgvector():
    """加载Excel数据到PostgreSQL pgvector"""
    print("="*60)
    print("1. 加载Excel数据到PostgreSQL pgvector")
    print("="*60)

    try:
        # 读取Excel文件
        df = pd.read_excel(EXCEL_FILE)
        print(f"✅ 成功读取Excel文件，共 {len(df)} 行数据")
        print(f"列名: {list(df.columns)}")

        # 准备批量插入的数据
        documents = []
        for idx, row in df.iterrows():
            # 合并行数据为文本
            content_parts = []
            for col in df.columns:
                if pd.notna(row[col]):
                    content_parts.append(f"{col}: {row[col]}")

            content = "\n".join(content_parts)

            doc = {
                "id": f"excel_{idx}",
                "content": content,
                "metadata": {
                    "source": "历史菜谱源头.xlsx",
                    "row": idx,
                    "type": "pgvector_data"
                }
            }
            documents.append(doc)

        # 批量插入到ingest服务
        async with aiohttp.ClientSession() as session:
            url = f"{INGEST_URL}/api/v1/knowledge/ingest/batch"
            payload = {"documents": documents}

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 成功插入 {len(documents)} 条文档到pgvector")
                    print(f"   响应: {result}")
                else:
                    error_text = await response.text()
                    print(f"❌ 插入失败: HTTP {response.status}")
                    print(f"   错误: {error_text}")

    except Exception as e:
        print(f"❌ 处理Excel文件失败: {e}")
        import traceback
        traceback.print_exc()

async def load_text_to_milvus():
    """加载文本数据到Milvus向量库"""
    print("\n" + "="*60)
    print("2. 加载文本数据到Milvus向量库")
    print("="*60)

    try:
        # 读取文本文件
        with open(TEXT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"✅ 成功读取文本文件，大小: {len(content)} 字符")

        # 分段处理
        chunk_size = 500  # 每段500字符
        overlap = 50     # 重叠50字符

        documents = []
        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            if len(chunk.strip()) > 50:  # 过滤太短的片段
                doc = {
                    "id": f"text_{i // (chunk_size - overlap)}",
                    "content": chunk,
                    "metadata": {
                        "source": "data.txt",
                        "chunk": i // (chunk_size - overlap),
                        "type": "milvus_data"
                    }
                }
                documents.append(doc)

        print(f"✅ 分成 {len(documents)} 个文档片段")

        # 批量插入到ingest服务
        async with aiohttp.ClientSession() as session:
            url = f"{INGEST_URL}/api/v1/knowledge/documents/batch"
            payload = {"documents": documents}

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 成功插入 {len(documents)} 条文档到Milvus")
                    print(f"   响应: {result}")
                else:
                    error_text = await response.text()
                    print(f"❌ 插入失败: HTTP {response.status}")
                    print(f"   错误: {error_text}")

    except Exception as e:
        print(f"❌ 处理文本文件失败: {e}")
        import traceback
        traceback.print_exc()

async def load_json_recipes():
    """加载recipe.json到向量库"""
    print("\n" + "="*60)
    print("3. 加载recipe.json到向量库")
    print("="*60)

    try:
        # 读取JSON文件
        with open("data/recipe.json", 'r', encoding='utf-8') as f:
            recipes = json.load(f)

        print(f"✅ 成功读取recipe.json，共 {len(recipes)} 条菜谱")

        # 准备文档
        documents = []
        for i, recipe in enumerate(recipes[:50]):  # 限制50条
            # 提取关键信息
            name = recipe.get("name", "")
            description = recipe.get("description", "")
            ingredients = recipe.get("ingredients", [])
            steps = recipe.get("steps", [])
            category = recipe.get("category", "")

            # 构建内容
            content = f"菜名: {name}\n"
            content += f"分类: {category}\n"
            content += f"描述: {description}\n"
            content += f"食材: {', '.join(ingredients[:10])}\n"  # 限制食材数量
            content += f"制作步骤: {'; '.join(steps[:5])}"  # 限制步骤数量

            doc = {
                "id": f"recipe_{recipe.get('_id', i)}",
                "content": content,
                "metadata": {
                    "source": "recipe.json",
                    "name": name,
                    "category": category,
                    "type": "recipe_data"
                }
            }
            documents.append(doc)

        print(f"✅ 准备了 {len(documents)} 条菜谱文档")

        # 批量插入到ingest服务
        async with aiohttp.ClientSession() as session:
            url = f"{INGEST_URL}/api/v1/knowledge/documents/batch"
            payload = {"documents": documents}

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 成功插入 {len(documents)} 条菜谱文档")
                    print(f"   响应: {result}")
                else:
                    error_text = await response.text()
                    print(f"❌ 插入失败: HTTP {response.status}")
                    print(f"   错误: {error_text}")

    except Exception as e:
        print(f"❌ 处理recipe.json失败: {e}")
        import traceback
        traceback.print_exc()

async def check_kb_stats():
    """检查知识库统计信息"""
    print("\n" + "="*60)
    print("4. 检查知识库统计信息")
    print("="*60)

    async with aiohttp.ClientSession() as session:
        url = f"{INGEST_URL}/api/v1/knowledge/stats"

        async with session.get(url) as response:
            if response.status == 200:
                stats = await response.json()
                print("✅ 知识库统计信息:")
                for key, value in stats.get("data", {}).items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ 获取统计信息失败: HTTP {response.status}")

async def test_search():
    """测试搜索功能"""
    print("\n" + "="*60)
    print("5. 测试搜索功能")
    print("="*60)

    test_queries = [
        "麻婆豆腐",
        "川菜历史",
        "宫保鸡丁做法",
        "菜谱文化"
    ]

    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n测试查询: {query}")
            print("-" * 40)

            url = f"{INGEST_URL}/api/v1/knowledge/search"
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
                            content = res.get("content", "")[:100]
                            source = res.get("metadata", {}).get("source", "未知")
                            print(f"  {i}. {content}... (来源: {source})")
                    else:
                        print("⚠️ 无结果")
                else:
                    print(f"❌ 搜索失败: HTTP {response.status}")

async def main():
    """主函数"""
    print("开始初始化知识库数据...")

    # 1. 加载Excel数据到pgvector
    await load_excel_to_pgvector()

    # 2. 加载文本数据到Milvus
    await load_text_to_milvus()

    # 3. 加载菜谱数据
    await load_json_recipes()

    # 等待索引建立
    print("\n等待索引建立...")
    await asyncio.sleep(3)

    # 4. 检查统计信息
    await check_kb_stats()

    # 5. 测试搜索
    await test_search()

    print("\n" + "="*60)
    print("初始化完成！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
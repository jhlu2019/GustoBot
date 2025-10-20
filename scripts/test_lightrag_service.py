"""
测试 LightRAG 服务

验证基于预生成索引文件的问答检索功能
"""

import asyncio
import inspect
from pathlib import Path

from app.services.lightrag_service import get_lightrag_service, LightRAGQueryRequest
from app.core.logger import get_logger

logger = get_logger(service="test-lightrag")


async def print_stream(stream):
    """打印流式响应"""
    print("", end="", flush=True)
    async for chunk in stream:
        print(chunk, end="", flush=True)
    print("\n")


async def test_query_modes():
    """测试所有查询模式"""
    service = get_lightrag_service()

    # 初始化服务
    await service.initialize()

    # 测试查询
    test_query = "红烧肉怎么做？"

    print("\n" + "=" * 60)
    print("LightRAG 服务测试")
    print("=" * 60)

    # 测试各种模式
    modes = ["naive", "local", "global", "hybrid"]

    for mode in modes:
        print(f"\n{'=' * 60}")
        print(f"Query mode: {mode}")
        print("=" * 60)

        try:
            # 非流式查询
            response = await service.query(
                query=test_query,
                mode=mode,
                stream=False,
            )
            print(f"\n回答:\n{response[:500]}...")  # 只显示前 500 字符
            print(f"\n完整响应长度: {len(response)} 字符")

        except Exception as e:
            logger.error(f"查询失败 ({mode}): {str(e)}", exc_info=True)


async def test_stream_query():
    """测试流式查询"""
    service = get_lightrag_service()

    await service.initialize()

    print("\n" + "=" * 60)
    print("流式查询测试 (hybrid mode)")
    print("=" * 60)

    try:
        response = await service.query(
            query="宫保鸡丁的做法",
            mode="hybrid",
            stream=True,
        )

        if inspect.isasyncgen(response):
            await print_stream(response)
        else:
            print(response)

    except Exception as e:
        logger.error(f"流式查询失败: {str(e)}", exc_info=True)


async def test_structured_query():
    """测试结构化查询"""
    service = get_lightrag_service()

    await service.initialize()

    print("\n" + "=" * 60)
    print("结构化查询测试")
    print("=" * 60)

    try:
        request = LightRAGQueryRequest(
            query="麻婆豆腐怎么做？",
            mode="hybrid",
            top_k=5,
            stream=False,
        )

        response = await service.query_structured(request)

        print(f"\n原始查询: {response.query}")
        print(f"检索模式: {response.mode}")
        print(f"元数据: {response.metadata}")
        print(f"\n回答:\n{response.response[:500]}...")

    except Exception as e:
        logger.error(f"结构化查询失败: {str(e)}", exc_info=True)


async def test_index_stats():
    """测试索引统计"""
    service = get_lightrag_service()

    print("\n" + "=" * 60)
    print("索引文件统计")
    print("=" * 60)

    stats = service.get_index_stats()

    print(f"\n工作目录: {stats['working_dir']}")
    print(f"总大小: {stats['total_size_mb']} MB")
    print(f"已初始化: {stats['initialized']}")
    print("\n文件详情:")

    for file_name, file_info in stats['files'].items():
        status = "✓" if file_info['exists'] else "✗"
        size = f"{file_info['size_mb']} MB" if file_info['exists'] else "N/A"
        print(f"  {status} {file_name}: {size}")


async def main():
    """主测试函数"""
    try:
        # 1. 检查索引文件统计
        await test_index_stats()

        # 2. 测试各种查询模式
        await test_query_modes()

        # 3. 测试流式查询
        await test_stream_query()

        # 4. 测试结构化查询
        await test_structured_query()

        print("\n" + "=" * 60)
        print("✓ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)
        raise

    finally:
        # 清理资源
        service = get_lightrag_service()
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

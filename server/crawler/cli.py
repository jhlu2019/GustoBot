"""
爬虫命令行工具
Crawler CLI Tool
"""
import asyncio
import argparse
import json
from pathlib import Path
from typing import List
from loguru import logger
from .wikipedia_crawler import WikipediaCrawler
from .recipe_crawler import RecipeCrawler
from .proxy_pool import ProxyPool
from .data_validator import DataValidator
from server.knowledge_base import KnowledgeService


async def crawl_wikipedia(
    queries: List[str],
    language: str = "zh",
    limit: int = 5,
    proxy_file: str = None,
    output: str = None
):
    """
    爬取Wikipedia菜谱

    Args:
        queries: 搜索关键词列表
        language: 语言代码
        limit: 每个查询的结果数量
        proxy_file: 代理文件路径
        output: 输出文件路径
    """
    logger.info(f"Starting Wikipedia crawler with queries: {queries}")

    # 初始化代理池
    proxy_pool = None
    if proxy_file:
        proxy_pool = ProxyPool.from_file(proxy_file)
        logger.info(f"Loaded proxy pool with {len(proxy_pool.proxies)} proxies")

    # 初始化爬虫
    crawler = WikipediaCrawler(
        language=language,
        proxy_pool=proxy_pool,
        request_delay=(2, 4)  # 更保守的延迟
    )

    # 运行爬虫
    recipes = await crawler.run(
        search_queries=queries,
        limit_per_query=limit
    )

    # 验证数据
    valid_recipes = DataValidator.validate_batch(recipes)

    # 去重
    unique_recipes = DataValidator.deduplicate(valid_recipes)

    logger.info(f"Crawled {len(unique_recipes)} unique valid recipes")

    # 保存结果
    if output:
        save_recipes(unique_recipes, output)

    return unique_recipes


async def crawl_urls(
    urls: List[str],
    proxy_file: str = None,
    output: str = None
):
    """
    爬取指定URL列表

    Args:
        urls: URL列表
        proxy_file: 代理文件路径
        output: 输出文件路径
    """
    logger.info(f"Starting URL crawler with {len(urls)} URLs")

    # 初始化代理池
    proxy_pool = None
    if proxy_file:
        proxy_pool = ProxyPool.from_file(proxy_file)

    # 初始化爬虫
    crawler = RecipeCrawler(
        proxy_pool=proxy_pool,
        request_delay=(1, 3)
    )

    # 运行爬虫
    recipes = await crawler.run(urls)

    # 验证数据
    valid_recipes = DataValidator.validate_batch(recipes)

    # 去重
    unique_recipes = DataValidator.deduplicate(valid_recipes)

    logger.info(f"Crawled {len(unique_recipes)} unique valid recipes")

    # 保存结果
    if output:
        save_recipes(unique_recipes, output)

    return unique_recipes


def save_recipes(recipes: List, output_path: str):
    """
    保存菜谱到文件

    Args:
        recipes: 菜谱列表
        output_path: 输出文件路径
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 转换为字典
    recipes_data = [recipe.dict() if hasattr(recipe, 'dict') else recipe for recipe in recipes]

    # 保存为JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recipes_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(recipes)} recipes to {output_path}")


async def import_to_knowledge_base(recipes: List, batch_size: int = 10):
    """
    将菜谱导入知识库

    Args:
        recipes: 菜谱列表
        batch_size: 批次大小
    """
    logger.info(f"Importing {len(recipes)} recipes to knowledge base...")

    service = KnowledgeService()

    # 转换为知识库格式
    kb_recipes = []
    for i, recipe in enumerate(recipes):
        recipe_data = recipe.dict() if hasattr(recipe, 'dict') else recipe

        # 添加ID
        recipe_data['id'] = recipe_data.get('id') or f"recipe_{i+1:06d}"

        kb_recipes.append(recipe_data)

    # 分批导入
    total_success = 0
    total_failed = 0

    for i in range(0, len(kb_recipes), batch_size):
        batch = kb_recipes[i:i + batch_size]
        result = await service.add_recipes_batch(batch)

        total_success += result.get('success', 0)
        total_failed += result.get('failed', 0)

        logger.info(f"Batch {i//batch_size + 1}: {result['success']} success, {result['failed']} failed")

    logger.info(f"Import completed: {total_success} success, {total_failed} failed")
    service.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="GustoBot Recipe Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 爬取Wikipedia中文菜谱
  python -m server.crawler.cli wikipedia --query "川菜" "粤菜" --limit 10

  # 爬取指定URL
  python -m server.crawler.cli urls --urls "https://example.com/recipe1" "https://example.com/recipe2"

  # 使用代理
  python -m server.crawler.cli wikipedia --query "中国菜" --proxy proxies.txt

  # 直接导入到知识库
  python -m server.crawler.cli wikipedia --query "家常菜" --import-kb

  # 保存到文件
  python -m server.crawler.cli wikipedia --query "烘焙" --output recipes.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Crawler command')

    # Wikipedia爬虫
    wiki_parser = subparsers.add_parser('wikipedia', help='Crawl Wikipedia recipes')
    wiki_parser.add_argument('--query', '-q', nargs='+', required=True, help='Search queries')
    wiki_parser.add_argument('--language', '-l', default='zh', help='Language code (default: zh)')
    wiki_parser.add_argument('--limit', '-n', type=int, default=5, help='Results per query (default: 5)')
    wiki_parser.add_argument('--proxy', '-p', help='Proxy file path')
    wiki_parser.add_argument('--output', '-o', help='Output JSON file path')
    wiki_parser.add_argument('--import-kb', action='store_true', help='Import to knowledge base')

    # URL爬虫
    url_parser = subparsers.add_parser('urls', help='Crawl recipe URLs')
    url_parser.add_argument('--urls', '-u', nargs='+', required=True, help='Recipe URLs')
    url_parser.add_argument('--proxy', '-p', help='Proxy file path')
    url_parser.add_argument('--output', '-o', help='Output JSON file path')
    url_parser.add_argument('--import-kb', action='store_true', help='Import to knowledge base')

    # 从文件导入到知识库
    import_parser = subparsers.add_parser('import', help='Import recipes from JSON file to knowledge base')
    import_parser.add_argument('--file', '-f', required=True, help='Input JSON file path')
    import_parser.add_argument('--batch-size', '-b', type=int, default=10, help='Batch size (default: 10)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 运行爬虫
    if args.command == 'wikipedia':
        recipes = asyncio.run(crawl_wikipedia(
            queries=args.query,
            language=args.language,
            limit=args.limit,
            proxy_file=args.proxy,
            output=args.output
        ))

        if args.import_kb:
            asyncio.run(import_to_knowledge_base(recipes))

    elif args.command == 'urls':
        recipes = asyncio.run(crawl_urls(
            urls=args.urls,
            proxy_file=args.proxy,
            output=args.output
        ))

        if args.import_kb:
            asyncio.run(import_to_knowledge_base(recipes))

    elif args.command == 'import':
        with open(args.file, 'r', encoding='utf-8') as f:
            recipes = json.load(f)

        asyncio.run(import_to_knowledge_base(recipes, batch_size=args.batch_size))


if __name__ == '__main__':
    main()

# GustoBot 爬虫实战示例

本文档提供了多个实战爬虫示例，涵盖不同场景和网站类型。

## 📚 目录

- [示例1: 下厨房网站爬虫](#示例1-下厨房网站爬虫)
- [示例2: 豆果美食爬虫](#示例2-豆果美食爬虫)
- [示例3: 美食杰爬虫](#示例3-美食杰爬虫)
- [示例4: Schema.org标准网站](#示例4-schemaorg标准网站)
- [示例5: 两阶段爬取模式](#示例5-两阶段爬取模式)
- [示例6: MongoDB集成](#示例6-mongodb集成)
- [示例7: 批量爬取与去重](#示例7-批量爬取与去重)
- [示例8: 下载图片](#示例8-下载图片)

---

## 示例1: 下厨房网站爬虫

下厨房是典型的需要JavaScript渲染的网站，需要使用浏览器爬虫。

```python
"""
下厨房菜谱爬虫
网站: https://www.xiachufang.com/
特点:
- 需要滚动加载完整步骤
- 食材和步骤分别在不同的区域
- 有用户评论区需要点击"展开"
"""
from gustobot.crawler.browser_crawler import BrowserCrawler
from gustobot.crawler.proxy_pool import ProxyPool
from lxml import etree
from typing import List, Dict
import json


class XiachufangCrawler(BrowserCrawler):
    """下厨房爬虫"""

    def __init__(self, **kwargs):
        super().__init__(
            name="XiachufangCrawler",
            headless=True,
            request_delay=(2, 4),
            max_retries=3,
            **kwargs
        )

    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """解析菜谱详情页"""
        tree = etree.HTML(html_content)

        try:
            # 基本信息
            name = tree.xpath('//h1[@class="page-title"]/text()')[0].strip()

            # 食材（分为主料和辅料）
            ingredients = []
            # 主料
            main_ingredients = tree.xpath('//div[@class="ingredients"]//tr')
            for ing in main_ingredients:
                name_elem = ing.xpath('.//td[@class="name"]/text()')
                amount_elem = ing.xpath('.//td[@class="unit"]/text()')
                if name_elem and amount_elem:
                    ingredients.append(f"{name_elem[0].strip()} {amount_elem[0].strip()}")

            # 步骤
            steps = []
            step_elements = tree.xpath('//div[@class="steps"]//li[@class="step"]')
            for i, step in enumerate(step_elements, 1):
                text = step.xpath('.//p[@class="text"]/text()')
                img = step.xpath('.//img/@src')
                steps.append({
                    "step": i,
                    "description": text[0].strip() if text else "",
                    "image": img[0] if img else ""
                })

            # 小贴士
            tips = tree.xpath('//div[@class="tip"]//p/text()')
            tips_text = tips[0].strip() if tips else ""

            # 难度、时间、人份
            stats = tree.xpath('//div[@class="recipe-stats"]//span/text()')
            difficulty = stats[0].strip() if len(stats) > 0 else ""
            time = stats[1].strip() if len(stats) > 1 else ""
            servings = stats[2].strip() if len(stats) > 2 else ""

            recipe = {
                "name": name,
                "ingredients": ingredients,
                "steps": steps,
                "tips": tips_text,
                "difficulty": difficulty,
                "time": time,
                "servings": servings,
                "url": url,
                "source": "下厨房"
            }

            return [recipe]

        except Exception as e:
            self.logger.error(f"解析失败 {url}: {e}")
            return []

    async def run(self, urls: List[str]) -> List[Dict]:
        """执行爬取"""
        self.start_stats()
        recipes = []

        for url in urls:
            html = await self.fetch_page(
                url,
                wait_selector='div.recipe-show',  # 等待主内容加载
                scroll_count=2,                    # 滚动加载图片
                click_selectors=[                  # 点击"展开更多"
                    '//a[contains(text(), "展开全部")]'
                ]
            )

            if html:
                parsed = await self.parse(html, url)
                recipes.extend(parsed)
                self.stats["items_scraped"] += len(parsed)

        self.end_stats()
        return recipes


# 使用示例
async def main():
    proxy_pool = ProxyPool.from_file("proxies.txt")
    crawler = XiachufangCrawler(proxy_pool=proxy_pool)

    async with crawler:
        recipes = await crawler.run([
            "https://www.xiachufang.com/recipe/12345/",
            "https://www.xiachufang.com/recipe/67890/"
        ])

        # 保存结果
        with open("xiachufang_recipes.json", "w", encoding="utf-8") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)

        print(f"爬取成功: {len(recipes)} 个菜谱")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 示例2: 豆果美食爬虫

豆果美食有较强的反爬机制，需要使用代理和合理的延迟。

```python
"""
豆果美食爬虫
网站: https://www.douguo.com/
特点:
- 有反爬机制，需要代理
- 图片懒加载，需要滚动
- 评论区需要点击"查看更多"
"""
from gustobot.crawler.browser_crawler import BrowserCrawler
from lxml import etree
import re


class DouguoCrawler(BrowserCrawler):
    """豆果美食爬虫"""

    def __init__(self, **kwargs):
        super().__init__(
            name="DouguoCrawler",
            headless=True,
            request_delay=(3, 6),  # 较长延迟避免被封
            max_retries=3,
            **kwargs
        )

    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """解析菜谱页面"""
        tree = etree.HTML(html_content)

        try:
            # 菜谱名称
            name = tree.xpath('//h1[@class="recipe_name"]/text()')[0].strip()

            # 食材
            ingredients = []
            ing_items = tree.xpath('//div[@class="foodstuff"]//li')
            for item in ing_items:
                name_elem = item.xpath('.//a/text()')
                weight_elem = item.xpath('.//span/text()')
                if name_elem:
                    ing_name = name_elem[0].strip()
                    weight = weight_elem[0].strip() if weight_elem else ""
                    ingredients.append(f"{ing_name} {weight}".strip())

            # 步骤
            steps = []
            step_items = tree.xpath('//div[@class="steps"]//div[@class="step"]')
            for i, step in enumerate(step_items, 1):
                desc = step.xpath('.//div[@class="text"]/text()')
                img = step.xpath('.//img/@data-src | .//img/@src')
                steps.append({
                    "step": i,
                    "description": desc[0].strip() if desc else "",
                    "image": img[0] if img else ""
                })

            # 小贴士
            tips = tree.xpath('//div[@class="recipe_tips"]//p/text()')

            # 统计信息
            cook_time = tree.xpath('//span[@class="cook_time"]/text()')
            difficulty = tree.xpath('//span[@class="difficulty"]/text()')

            recipe = {
                "name": name,
                "ingredients": ingredients,
                "steps": steps,
                "tips": "\n".join([t.strip() for t in tips]),
                "time": cook_time[0].strip() if cook_time else "",
                "difficulty": difficulty[0].strip() if difficulty else "",
                "url": url,
                "source": "豆果美食"
            }

            return [recipe]

        except Exception as e:
            self.logger.error(f"解析失败: {e}")
            return []

    async def search_recipes(self, keyword: str, max_results: int = 10) -> List[str]:
        """搜索菜谱并返回URL列表"""
        search_url = f"https://www.douguo.com/search/recipe/{keyword}"

        html = await self.fetch_page(
            search_url,
            wait_selector='div.recipe_list',
            scroll_count=3
        )

        if not html:
            return []

        tree = etree.HTML(html)
        links = tree.xpath('//div[@class="recipe_item"]//a[@class="recipe_name"]/@href')

        # 补全URL并去重
        full_urls = list(set([
            f"https://www.douguo.com{link}" if link.startswith('/') else link
            for link in links[:max_results]
        ]))

        self.logger.info(f"搜索到 {len(full_urls)} 个菜谱")
        return full_urls

    async def run(self, keywords: List[str], max_per_keyword: int = 5):
        """运行爬虫"""
        self.start_stats()
        all_recipes = []

        for keyword in keywords:
            self.logger.info(f"正在搜索: {keyword}")

            # 第一步: 搜索获取URL
            urls = await self.search_recipes(keyword, max_per_keyword)

            # 第二步: 爬取详情页
            for url in urls:
                html = await self.fetch_page(
                    url,
                    wait_selector='div.recipe_content',
                    scroll_count=2
                )

                if html:
                    recipes = await self.parse(html, url)
                    all_recipes.extend(recipes)
                    self.stats["items_scraped"] += len(recipes)

        self.end_stats()
        return all_recipes


# 使用示例
async def main():
    from gustobot.crawler.proxy_pool import ProxyPool

    proxy_pool = ProxyPool.from_file("proxies.txt")
    crawler = DouguoCrawler(proxy_pool=proxy_pool)

    async with crawler:
        recipes = await crawler.run(
            keywords=["红烧肉", "糖醋排骨", "麻婆豆腐"],
            max_per_keyword=5
        )

        print(f"共爬取 {len(recipes)} 个菜谱")
```

---

## 示例3: 美食杰爬虫

使用HTTP爬虫的示例（静态页面）。

```python
"""
美食杰爬虫 (HTTP版本)
网站: https://www.meishij.net/
特点:
- 静态HTML，不需要浏览器
- 使用HTTP爬虫即可，速度快
"""
from gustobot.crawler import BaseCrawler
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict


class MeishijCrawler(BaseCrawler):
    """美食杰爬虫（HTTP版本）"""

    def __init__(self, **kwargs):
        super().__init__(
            name="MeishijCrawler",
            request_delay=(1, 3),
            max_retries=3,
            **kwargs
        )

    async def parse(self, response: httpx.Response) -> Dict:
        """解析响应"""
        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            # 菜谱名称
            name = soup.find('h1', class_='recipe_title').text.strip()

            # 食材
            ingredients = []
            ing_list = soup.find('div', class_='materials')
            if ing_list:
                for li in ing_list.find_all('li'):
                    ingredients.append(li.text.strip())

            # 步骤
            steps = []
            step_list = soup.find('div', class_='recipe_steps')
            if step_list:
                for i, step_div in enumerate(step_list.find_all('div', class_='step'), 1):
                    text = step_div.find('p', class_='text')
                    img = step_div.find('img')
                    steps.append({
                        "step": i,
                        "description": text.text.strip() if text else "",
                        "image": img['src'] if img else ""
                    })

            recipe = {
                "name": name,
                "ingredients": ingredients,
                "steps": steps,
                "url": str(response.url),
                "source": "美食杰"
            }

            return recipe

        except Exception as e:
            self.logger.error(f"解析失败: {e}")
            return None

    async def run(self, urls: List[str]) -> List[Dict]:
        """运行爬虫"""
        self.start_stats()
        recipes = []

        for url in urls:
            response = await self.fetch(url)
            if response:
                recipe = await self.parse(response)
                if recipe:
                    recipes.append(recipe)
                    self.stats["items_scraped"] += 1

        self.end_stats()
        return recipes


# 使用示例
async def main():
    crawler = MeishijCrawler()

    recipes = await crawler.run([
        "https://www.meishij.net/recipe/12345.html",
        "https://www.meishij.net/recipe/67890.html"
    ])

    print(f"爬取成功: {len(recipes)} 个菜谱")
```

---

## 示例4: Schema.org标准网站

使用内置的RecipeCrawler爬取符合Schema.org标准的网站。

```python
"""
Schema.org标准网站爬虫
适用于所有实现了Schema.org Recipe标准的网站
"""
from gustobot.crawler import RecipeCrawler
from gustobot.crawler.proxy_pool import ProxyPool


async def crawl_schema_org_sites():
    """爬取Schema.org标准网站"""

    # 创建爬虫（自动识别JSON-LD和Microdata）
    proxy_pool = ProxyPool.from_file("proxies.txt")
    crawler = RecipeCrawler(proxy_pool=proxy_pool)

    # 爬取多个网站
    urls = [
        "https://www.allrecipes.com/recipe/12345/",
        "https://www.food.com/recipe/67890/",
        "https://cooking.nytimes.com/recipes/12345-recipe"
    ]

    recipes = await crawler.run(urls)

    # 数据验证
    from gustobot.crawler.data_validator import DataValidator

    valid_recipes = DataValidator.validate_batch(recipes)
    unique_recipes = DataValidator.deduplicate(valid_recipes)

    print(f"爬取: {len(recipes)} 个")
    print(f"有效: {len(valid_recipes)} 个")
    print(f"去重: {len(unique_recipes)} 个")

    return unique_recipes


# 运行
if __name__ == "__main__":
    import asyncio
    asyncio.run(crawl_schema_org_sites())
```

---

## 示例5: 两阶段爬取模式

先爬列表页获取链接，再爬详情页获取数据。

```python
"""
两阶段爬取模式
Stage 1: 列表页 -> 收集URL
Stage 2: 详情页 -> 提取数据
"""
from gustobot.crawler.browser_crawler import BrowserCrawler
from lxml import etree
from typing import List


class TwoStageCrawler(BrowserCrawler):
    """两阶段爬虫"""

    async def crawl_list_page(self, list_url: str, max_pages: int = 5) -> List[str]:
        """
        第一阶段: 爬取列表页，收集菜谱URL

        Args:
            list_url: 列表页URL（可能是搜索结果或分类页）
            max_pages: 最大爬取页数

        Returns:
            菜谱URL列表
        """
        all_urls = []

        for page in range(1, max_pages + 1):
            # 构造分页URL
            paginated_url = f"{list_url}?page={page}"
            self.logger.info(f"正在爬取列表页 {page}/{max_pages}")

            html = await self.fetch_page(
                paginated_url,
                wait_selector='div.recipe-list',
                scroll_count=3  # 滚动加载更多
            )

            if not html:
                break

            # 提取链接
            tree = etree.HTML(html)
            links = tree.xpath('//div[@class="recipe-item"]//a/@href')

            if not links:
                self.logger.info("没有更多链接，停止爬取")
                break

            # 补全URL
            full_links = [
                f"https://example.com{link}" if link.startswith('/') else link
                for link in links
            ]

            all_urls.extend(full_links)
            self.logger.info(f"从第{page}页提取了 {len(full_links)} 个链接")

        # 去重
        unique_urls = list(set(all_urls))
        self.logger.info(f"总共收集到 {len(unique_urls)} 个唯一链接")

        return unique_urls

    async def crawl_detail_page(self, url: str):
        """
        第二阶段: 爬取详情页，提取菜谱数据
        """
        html = await self.fetch_page(
            url,
            wait_selector='div.recipe-content',
            scroll_count=2,
            click_selectors=['//button[contains(text(), "展开")]']
        )

        if html:
            return await self.parse(html, url)
        return None

    async def parse(self, html_content: str, url: str):
        """解析详情页"""
        # 实现解析逻辑
        pass

    async def run(self, list_url: str, max_pages: int = 5, max_recipes: int = 50):
        """
        完整的两阶段爬取流程

        Args:
            list_url: 列表页URL
            max_pages: 最大列表页数
            max_recipes: 最大菜谱数
        """
        self.start_stats()

        # 第一阶段: 收集URL
        self.logger.info("=" * 60)
        self.logger.info("第一阶段: 爬取列表页，收集菜谱链接")
        self.logger.info("=" * 60)

        recipe_urls = await self.crawl_list_page(list_url, max_pages)

        # 第二阶段: 爬取详情
        self.logger.info("=" * 60)
        self.logger.info("第二阶段: 爬取详情页，提取菜谱数据")
        self.logger.info("=" * 60)

        recipes = []
        for i, url in enumerate(recipe_urls[:max_recipes], 1):
            self.logger.info(f"正在爬取 ({i}/{min(len(recipe_urls), max_recipes)}): {url}")

            recipe = await self.crawl_detail_page(url)
            if recipe:
                recipes.append(recipe)
                self.stats["items_scraped"] += 1

        self.end_stats()
        return recipes


# 使用示例
async def main():
    from gustobot.crawler.proxy_pool import ProxyPool

    proxy_pool = ProxyPool.from_file("proxies.txt")
    crawler = TwoStageCrawler(proxy_pool=proxy_pool, headless=True)

    async with crawler:
        recipes = await crawler.run(
            list_url="https://example.com/recipes",
            max_pages=5,
            max_recipes=50
        )

        print(f"成功爬取 {len(recipes)} 个菜谱")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 示例6: MongoDB集成

将爬取的数据直接保存到MongoDB。

```python
"""
MongoDB集成示例
实时保存爬取结果，避免数据丢失
"""
from gustobot.crawler.browser_crawler import BrowserCrawler
from pymongo import MongoClient
from datetime import datetime


class MongoRecipeCrawler(BrowserCrawler):
    """MongoDB集成爬虫"""

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "recipe_db",
        collection_name: str = "recipes",
        **kwargs
    ):
        super().__init__(name="MongoRecipeCrawler", **kwargs)

        # 连接MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        # 创建唯一索引（避免重复）
        self.collection.create_index("url", unique=True)

        self.logger.info(f"已连接MongoDB: {mongo_uri} / {db_name}.{collection_name}")

    def save_recipe(self, recipe: dict) -> bool:
        """
        保存菜谱到MongoDB

        Returns:
            True: 保存成功
            False: 已存在，跳过
        """
        try:
            # 添加时间戳
            recipe["crawled_at"] = datetime.now()
            recipe["updated_at"] = datetime.now()

            # 插入（如果URL已存在会抛出异常）
            self.collection.insert_one(recipe)
            self.logger.info(f"✅ 已保存: {recipe['name']}")
            return True

        except Exception as e:
            if "duplicate key error" in str(e):
                self.logger.info(f"⏭️  已存在，跳过: {recipe.get('name', 'Unknown')}")
            else:
                self.logger.error(f"❌ 保存失败: {e}")
            return False

    def recipe_exists(self, url: str) -> bool:
        """检查菜谱是否已存在"""
        return self.collection.find_one({"url": url}) is not None

    async def parse(self, html_content: str, url: str):
        """解析页面"""
        # 实现解析逻辑
        recipe = {
            "name": "示例菜谱",
            "url": url,
            "source": "示例网站"
        }
        return [recipe]

    async def run(self, urls: List[str], skip_existing: bool = True):
        """
        运行爬虫

        Args:
            urls: URL列表
            skip_existing: 是否跳过已存在的URL
        """
        self.start_stats()

        for i, url in enumerate(urls, 1):
            # 检查是否已存在
            if skip_existing and self.recipe_exists(url):
                self.logger.info(f"({i}/{len(urls)}) 已存在，跳过: {url}")
                continue

            self.logger.info(f"({i}/{len(urls)}) 正在爬取: {url}")

            # 爬取页面
            html = await self.fetch_page(url, scroll_count=2)
            if html:
                recipes = await self.parse(html, url)

                # 保存到MongoDB
                for recipe in recipes:
                    if self.save_recipe(recipe):
                        self.stats["items_scraped"] += 1

        self.end_stats()

        # 返回统计信息
        total_count = self.collection.count_documents({})
        return {
            "crawled": self.stats["items_scraped"],
            "total_in_db": total_count
        }

    def close(self):
        """关闭MongoDB连接"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB连接已关闭")


# 使用示例
async def main():
    crawler = MongoRecipeCrawler(
        mongo_uri="mongodb://localhost:27017/",
        db_name="recipe_db",
        collection_name="recipes",
        headless=True
    )

    try:
        async with crawler:
            result = await crawler.run(
                urls=["https://example.com/recipe1", "https://example.com/recipe2"],
                skip_existing=True
            )

            print(f"本次爬取: {result['crawled']} 个")
            print(f"数据库总数: {result['total_in_db']} 个")

    finally:
        crawler.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 示例7: 批量爬取与去重

处理大量URL并自动去重。

```python
"""
批量爬取与去重示例
"""
import asyncio
from gustobot.crawler.browser_crawler import BrowserCrawler
from gustobot.crawler.data_validator import DataValidator
from typing import List, Set
import json


class BatchCrawler(BrowserCrawler):
    """批量爬虫"""

    def __init__(self, **kwargs):
        super().__init__(name="BatchCrawler", **kwargs)
        self.seen_urls: Set[str] = set()  # 已爬取的URL

    async def parse(self, html_content: str, url: str):
        """解析页面"""
        # 实现解析逻辑
        pass

    async def crawl_batch(
        self,
        urls: List[str],
        batch_size: int = 10,
        concurrent: int = 3
    ) -> List[dict]:
        """
        批量爬取

        Args:
            urls: URL列表
            batch_size: 每批处理数量
            concurrent: 并发数
        """
        all_recipes = []

        # 分批处理
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            self.logger.info(f"正在处理第 {i//batch_size + 1} 批 ({len(batch)} 个URL)")

            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(concurrent)

            async def fetch_one(url):
                # 跳过已爬取的URL
                if url in self.seen_urls:
                    self.logger.info(f"跳过重复URL: {url}")
                    return None

                async with semaphore:
                    self.seen_urls.add(url)
                    html = await self.fetch_page(url, scroll_count=2)
                    if html:
                        return await self.parse(html, url)
                    return None

            # 并发爬取
            tasks = [fetch_one(url) for url in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 收集结果
            for result in results:
                if result and not isinstance(result, Exception):
                    all_recipes.extend(result)

            self.logger.info(f"第 {i//batch_size + 1} 批完成，已爬取 {len(all_recipes)} 个菜谱")

        return all_recipes

    async def run(self, urls: List[str]) -> List[dict]:
        """运行爬虫"""
        self.start_stats()

        # 批量爬取
        recipes = await self.crawl_batch(urls, batch_size=10, concurrent=3)

        # 数据验证和去重
        self.logger.info("正在验证和去重...")
        valid_recipes = DataValidator.validate_batch(recipes)
        unique_recipes = DataValidator.deduplicate(valid_recipes)

        self.stats["items_scraped"] = len(unique_recipes)
        self.end_stats()

        self.logger.info(f"原始: {len(recipes)}, 有效: {len(valid_recipes)}, 去重: {len(unique_recipes)}")

        return [r.dict() for r in unique_recipes]


# 使用示例
async def main():
    # 从文件加载URL列表
    with open("urls.txt", "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    crawler = BatchCrawler(headless=True)

    async with crawler:
        recipes = await crawler.run(urls)

        # 保存结果
        with open("recipes_batch.json", "w", encoding="utf-8") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)

        print(f"成功爬取并去重: {len(recipes)} 个菜谱")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 示例8: 下载图片

爬取菜谱并下载相关图片。

```python
"""
下载图片示例
"""
from gustobot.crawler.browser_crawler import BrowserCrawler
import httpx
import os
from pathlib import Path
import hashlib
from urllib.parse import urlparse


class ImageDownloadCrawler(BrowserCrawler):
    """带图片下载功能的爬虫"""

    def __init__(self, image_dir: str = "images", **kwargs):
        super().__init__(name="ImageDownloadCrawler", **kwargs)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(exist_ok=True)

    async def download_image(self, url: str, filename: str = None) -> str:
        """
        下载图片

        Args:
            url: 图片URL
            filename: 保存文件名（可选，默认使用URL哈希）

        Returns:
            本地文件路径
        """
        if not url:
            return ""

        try:
            # 生成文件名
            if not filename:
                url_hash = hashlib.md5(url.encode()).hexdigest()
                ext = Path(urlparse(url).path).suffix or '.jpg'
                filename = f"{url_hash}{ext}"

            filepath = self.image_dir / filename

            # 如果文件已存在，跳过下载
            if filepath.exists():
                self.logger.debug(f"图片已存在: {filepath}")
                return str(filepath)

            # 下载图片
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                response.raise_for_status()

                # 保存文件
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                self.logger.info(f"✅ 已下载: {filepath}")
                return str(filepath)

        except Exception as e:
            self.logger.error(f"下载图片失败 {url}: {e}")
            return ""

    async def parse(self, html_content: str, url: str):
        """解析页面并下载图片"""
        from lxml import etree

        tree = etree.HTML(html_content)

        # 提取基本信息
        name = tree.xpath('//h1[@class="title"]/text()')[0].strip()

        # 主图
        main_image_url = tree.xpath('//img[@class="main-image"]/@src')[0]
        main_image_path = await self.download_image(main_image_url, f"{name}_main.jpg")

        # 步骤图
        steps = []
        step_elements = tree.xpath('//div[@class="steps"]//div[@class="step"]')
        for i, step in enumerate(step_elements, 1):
            desc = step.xpath('.//p/text()')[0].strip()
            img_url = step.xpath('.//img/@src')[0] if step.xpath('.//img/@src') else ""

            # 下载步骤图
            img_path = await self.download_image(img_url, f"{name}_step{i}.jpg") if img_url else ""

            steps.append({
                "step": i,
                "description": desc,
                "image_url": img_url,
                "image_path": img_path
            })

        recipe = {
            "name": name,
            "main_image_url": main_image_url,
            "main_image_path": main_image_path,
            "steps": steps,
            "url": url
        }

        return [recipe]

    async def run(self, urls: List[str]):
        """运行爬虫"""
        self.start_stats()
        recipes = []

        for url in urls:
            html = await self.fetch_page(url, scroll_count=2)
            if html:
                parsed = await self.parse(html, url)
                recipes.extend(parsed)
                self.stats["items_scraped"] += len(parsed)

        self.end_stats()

        self.logger.info(f"爬取完成，图片保存在: {self.image_dir}")
        return recipes


# 使用示例
async def main():
    crawler = ImageDownloadCrawler(
        image_dir="downloaded_images",
        headless=True
    )

    async with crawler:
        recipes = await crawler.run([
            "https://example.com/recipe1",
            "https://example.com/recipe2"
        ])

        # 统计
        total_images = sum(
            1 + len(r['steps'])  # 主图 + 步骤图
            for r in recipes
        )

        print(f"爬取: {len(recipes)} 个菜谱")
        print(f"下载: {total_images} 张图片")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 总结

以上示例涵盖了：

1. ✅ **不同网站类型**: 动态页面、静态页面、Schema.org标准
2. ✅ **不同爬取模式**: 单页、列表+详情、搜索+详情
3. ✅ **数据存储**: JSON文件、MongoDB
4. ✅ **高级功能**: 批量处理、并发控制、图片下载
5. ✅ **反爬机制**: 代理池、延迟、重试

你可以根据目标网站的特点，选择合适的示例作为起点，进行定制化开发。

---

**更多文档**:
- [爬虫使用指南](crawler_guide.md)
- [反爬虫最佳实践](anti_scraping_guide.md)

祝你爬取愉快！ 🕷️

# GustoBot 爬虫使用指南

## 📚 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [爬虫类型](#爬虫类型)
- [代理池配置](#代理池配置)
- [命令行工具](#命令行工具)
- [自定义爬虫开发](#自定义爬虫开发)
- [数据验证与清洗](#数据验证与清洗)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

GustoBot爬虫模块是一个企业级的网页数据采集框架，专为菜谱数据采集设计，但可扩展用于其他类型网站。

### 核心特性

✅ **双引擎架构**
- **HTTP爬虫** (BaseCrawler): 基于httpx，适用于静态页面，速度快
- **浏览器爬虫** (BrowserCrawler): 基于Playwright，适用于动态页面，功能强大

✅ **完善的反爬机制**
- IP代理池（自动轮换、健康检查）
- 随机User-Agent池
- 请求延迟（可配置范围）
- 失败重试（指数退避）
- Robots.txt遵守

✅ **数据质量保障**
- Pydantic模型验证
- 自动数据清洗
- 去重处理
- 时间格式规范化

✅ **多数据源支持**
- Wikipedia API
- Schema.org标准网站（JSON-LD、Microdata）
- 通用HTML页面（启发式解析）

---

## 快速开始

### 安装依赖

爬虫模块需要额外的依赖：

```bash
# 基础HTTP爬虫
pip install httpx beautifulsoup4 lxml fake-useragent pydantic

# 浏览器爬虫（需要安装Playwright）
pip install playwright
playwright install chromium  # 安装Chromium浏览器
```

### 第一个爬虫示例

**示例1: 使用命令行工具爬取Wikipedia**

```bash
python -m gustobot.crawler.cli wikipedia --query "红烧肉" --limit 5
```

**示例2: 使用Python代码**

```python
import asyncio
from gustobot.crawler import WikipediaCrawler

async def main():
    # 创建爬虫实例
    crawler = WikipediaCrawler(language="zh")

    # 执行爬取
    recipes = await crawler.run(
        search_queries=["川菜", "粤菜"],
        limit_per_query=5
    )

    print(f"成功爬取 {len(recipes)} 个菜谱")
    for recipe in recipes:
        print(f"- {recipe['name']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 爬虫类型

### 1. HTTP爬虫 (BaseCrawler)

**适用场景**: 静态HTML页面，内容直接包含在HTML源码中

**优点**: 速度快，资源消耗低

**缺点**: 无法处理JavaScript动态内容

**示例**:

```python
from gustobot.crawler import BaseCrawler
import httpx

class SimpleRecipeCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(
            name="SimpleRecipeCrawler",
            request_delay=(1, 3),  # 1-3秒随机延迟
            max_retries=3
        )

    async def parse(self, response: httpx.Response):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取数据
        recipe = {
            "name": soup.find('h1', class_='title').text.strip(),
            "ingredients": [li.text for li in soup.find_all('li', class_='ingredient')],
            "steps": [p.text for p in soup.find_all('p', class_='step')]
        }
        return recipe

    async def run(self, urls):
        self.start_stats()
        recipes = []

        for url in urls:
            response = await self.fetch(url)
            if response:
                recipe = await self.parse(response)
                recipes.append(recipe)
                self.stats["items_scraped"] += 1

        self.end_stats()
        return recipes
```

### 2. 浏览器爬虫 (BrowserCrawler)

**适用场景**: 需要JavaScript渲染的动态页面

**优点**: 功能强大，可模拟用户行为

**缺点**: 速度慢，资源消耗高

**核心功能**:
- ✅ JavaScript渲染
- ✅ 页面滚动（触发懒加载）
- ✅ 元素点击（展开按钮等）
- ✅ 等待元素加载
- ✅ 执行自定义JS代码
- ✅ 页面截图

**示例**:

```python
from gustobot.crawler.browser_crawler import BrowserCrawler
from lxml import etree

class DynamicRecipeCrawler(BrowserCrawler):
    def __init__(self, **kwargs):
        super().__init__(
            name="DynamicRecipeCrawler",
            headless=True,           # 无头模式
            request_delay=(2, 4),    # 2-4秒延迟
            **kwargs
        )

    async def parse(self, html_content: str, url: str):
        tree = etree.HTML(html_content)

        recipe = {
            "name": tree.xpath('//h1[@class="title"]/text()')[0].strip(),
            "ingredients": tree.xpath('//div[@class="ingredients"]//li/text()'),
            "steps": tree.xpath('//div[@class="steps"]//p/text()'),
            "url": url
        }
        return [recipe]

    async def run(self, urls):
        self.start_stats()
        recipes = []

        for url in urls:
            # 加载页面，滚动3次，点击"展开"按钮
            html = await self.fetch_page(
                url,
                wait_selector='div.recipe-content',  # 等待内容加载
                scroll_count=3,                       # 滚动3次
                click_selectors=[                     # 点击展开按钮
                    '//button[contains(text(), "展开")]',
                    '//button[contains(text(), "查看更多")]'
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
    crawler = DynamicRecipeCrawler(headless=True)

    # 使用async with自动管理浏览器生命周期
    async with crawler:
        recipes = await crawler.run([
            "https://example.com/recipe1",
            "https://example.com/recipe2"
        ])

    print(f"爬取了 {len(recipes)} 个菜谱")
```

### 3. 混合爬虫 (HybridCrawler)

结合HTTP爬虫和浏览器爬虫的优势：
- 列表页用HTTP（快速）
- 详情页用浏览器（功能强大）

```python
from gustobot.crawler.browser_crawler import HybridCrawler

class HybridRecipeCrawler(HybridCrawler):
    async def run(self, list_url):
        # 第一阶段: 用HTTP快速获取列表页
        list_html = await self.fetch_static(list_url)
        recipe_urls = self.extract_urls(list_html)

        # 第二阶段: 用浏览器渲染详情页
        recipes = []
        for url in recipe_urls:
            html = await self.fetch_page(url, scroll_count=2)
            recipes.extend(await self.parse(html, url))

        return recipes
```

---

## 代理池配置

### 为什么需要代理池？

1. **避免IP封禁**: 频繁请求同一网站可能被封IP
2. **突破访问限制**: 某些网站限制单IP请求频率
3. **地域限制**: 访问有地域限制的内容

### 代理配置格式

创建`proxies.txt`文件，支持多种格式：

```txt
# 格式1: host:port
127.0.0.1:8080
192.168.1.100:3128

# 格式2: host:port:username:password
proxy.example.com:8080:myuser:mypass

# 格式3: protocol://host:port
http://127.0.0.1:8080
https://proxy.example.com:443

# 格式4: protocol://username:password@host:port
http://user:pass@proxy.example.com:8080
socks5://user:pass@socks-proxy.com:1080

# 注释行（以#开头）会被忽略
# 空行也会被忽略
```

### 使用代理池

**方法1: 从文件加载**

```python
from gustobot.crawler.proxy_pool import ProxyPool
from gustobot.crawler.browser_crawler import BrowserCrawler

# 加载代理池
proxy_pool = ProxyPool.from_file("proxies.txt")

# 在爬虫中使用
crawler = BrowserCrawler(
    name="MyCrawler",
    proxy_pool=proxy_pool
)
```

**方法2: 手动添加**

```python
from gustobot.crawler.proxy_pool import ProxyPool

proxy_pool = ProxyPool(
    check_interval=300,   # 健康检查间隔(秒)
    max_fail_count=5,     # 最大失败次数
    timeout=10.0          # 代理测试超时
)

# 添加代理
proxy_pool.add_proxy(host="127.0.0.1", port=8080)
proxy_pool.add_proxy(
    host="proxy.example.com",
    port=8080,
    username="user",
    password="pass"
)
```

### 代理池管理

```python
import asyncio
from gustobot.crawler.proxy_pool import ProxyPool

async def manage_proxies():
    proxy_pool = ProxyPool.from_file("proxies.txt")

    # 手动健康检查
    await proxy_pool.health_check()

    # 查看统计信息
    stats = proxy_pool.get_stats()
    print(f"总代理数: {stats['total_proxies']}")
    print(f"活跃代理: {stats['active_proxies']}")
    print(f"平均成功率: {stats['average_success_rate']:.2%}")
    print(f"平均响应时间: {stats['average_response_time']:.2f}s")

    # 启动自动健康检查循环（每5分钟）
    asyncio.create_task(proxy_pool.start_health_check_loop())
```

---

## 命令行工具

### Wikipedia爬取

```bash
# 基础用法
python -m gustobot.crawler.cli wikipedia --query "川菜" "粤菜"

# 指定语言和数量
python -m gustobot.crawler.cli wikipedia \
  --query "中国菜" \
  --language zh \
  --limit 10

# 使用代理
python -m gustobot.crawler.cli wikipedia \
  --query "烘焙" \
  --proxy proxies.txt

# 保存到文件
python -m gustobot.crawler.cli wikipedia \
  --query "家常菜" \
  --output recipes.json

# 直接导入到知识库
python -m gustobot.crawler.cli wikipedia \
  --query "甜品" \
  --import-kb
```

### URL爬取

```bash
# 爬取指定URL
python -m gustobot.crawler.cli urls \
  --urls "https://example.com/recipe1" "https://example.com/recipe2"

# 使用代理并保存
python -m gustobot.crawler.cli urls \
  --urls "https://example.com/recipes" \
  --proxy proxies.txt \
  --output output.json

# 直接导入知识库
python -m gustobot.crawler.cli urls \
  --urls "https://example.com/recipe" \
  --import-kb
```

### 从文件导入

```bash
# 将JSON文件导入知识库
python -m gustobot.crawler.cli import \
  --file recipes.json \
  --batch-size 20
```

---

## 自定义爬虫开发

### 开发步骤

1. **选择基类**: `BaseCrawler` (HTTP) 或 `BrowserCrawler` (浏览器)
2. **实现parse方法**: 解析HTML提取数据
3. **实现run方法**: 爬取逻辑
4. **配置反爬参数**: 代理、延迟、重试等

### 完整示例: 美食天下爬虫

```python
from gustobot.crawler.browser_crawler import BrowserCrawler
from gustobot.crawler.proxy_pool import ProxyPool
from lxml import etree
from typing import List, Dict
from loguru import logger

class MeishitianxiaCrawler(BrowserCrawler):
    """美食天下菜谱爬虫

    网站特点:
    - 列表页: 分页显示，每页15个菜谱
    - 详情页: 需要滚动加载完整步骤图
    - 反爬: 有访问频率限制，需要代理池
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="MeishitianxiaCrawler",
            headless=True,           # 无头模式
            request_delay=(3, 6),    # 3-6秒随机延迟（避免被封）
            max_retries=3,           # 最大重试3次
            timeout=60000,           # 60秒超时
            **kwargs
        )

    async def parse_list_page(self, html_content: str) -> List[str]:
        """解析列表页，提取菜谱链接"""
        tree = etree.HTML(html_content)

        # XPath提取链接
        links = tree.xpath('//div[@class="recipe-item"]//a/@href')

        # 补全URL
        full_urls = [
            f"https://www.meishitianxia.com{link}"
            if link.startswith('/') else link
            for link in links
        ]

        logger.info(f"从列表页提取了 {len(full_urls)} 个链接")
        return full_urls

    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """解析详情页，提取菜谱数据"""
        tree = etree.HTML(html_content)

        try:
            recipe = {
                "name": tree.xpath('//h1[@class="recipe-title"]/text()')[0].strip(),
                "category": tree.xpath('//span[@class="category"]/text()')[0].strip(),
                "difficulty": tree.xpath('//span[@class="difficulty"]/text()')[0].strip(),
                "time": tree.xpath('//span[@class="time"]/text()')[0].strip(),

                # 食材列表
                "ingredients": [
                    ing.strip()
                    for ing in tree.xpath('//div[@class="ingredients"]//li/text()')
                    if ing.strip()
                ],

                # 步骤（包含图片）
                "steps": [
                    {
                        "step": i + 1,
                        "description": step.strip(),
                        "image": tree.xpath(f'//div[@class="steps"]//div[@data-step="{i+1}"]//img/@src')
                    }
                    for i, step in enumerate(tree.xpath('//div[@class="steps"]//p/text()'))
                ],

                # 小贴士
                "tips": tree.xpath('//div[@class="tips"]/text()')[0].strip()
                        if tree.xpath('//div[@class="tips"]/text()') else "",

                # 主图
                "image": tree.xpath('//img[@class="recipe-main-img"]/@src')[0],

                # 元数据
                "url": url,
                "source": "美食天下"
            }

            logger.info(f"成功解析菜谱: {recipe['name']}")
            return [recipe]

        except Exception as e:
            logger.error(f"解析失败 {url}: {e}")
            return []

    async def run(
        self,
        category_urls: List[str],
        max_recipes: int = 100,
        save_to_db: bool = False
    ) -> List[Dict]:
        """
        运行爬虫

        Args:
            category_urls: 分类页URL列表
            max_recipes: 最大爬取数量
            save_to_db: 是否保存到数据库

        Returns:
            菜谱列表
        """
        self.start_stats()
        all_recipes = []

        # 第一阶段: 获取所有菜谱URL
        logger.info("第一阶段: 爬取列表页，收集菜谱链接...")
        recipe_urls = []

        for category_url in category_urls:
            # 爬取列表页（可能需要滚动加载更多）
            html = await self.fetch_page(
                category_url,
                wait_selector='div.recipe-item',  # 等待列表项加载
                scroll_count=3                     # 滚动3次加载更多
            )

            if html:
                urls = await self.parse_list_page(html)
                recipe_urls.extend(urls)

                # 达到数量上限则停止
                if len(recipe_urls) >= max_recipes:
                    break

        logger.info(f"收集到 {len(recipe_urls)} 个菜谱链接")

        # 第二阶段: 爬取详情页
        logger.info("第二阶段: 爬取详情页，提取菜谱数据...")

        for i, url in enumerate(recipe_urls[:max_recipes], 1):
            logger.info(f"正在爬取 ({i}/{min(len(recipe_urls), max_recipes)}): {url}")

            # 爬取详情页
            html = await self.fetch_page(
                url,
                wait_selector='div.recipe-content',  # 等待内容加载
                scroll_count=2,                       # 滚动加载完整步骤图
                click_selectors=[                     # 点击展开按钮
                    '//button[contains(text(), "展开全部步骤")]',
                    '//a[contains(text(), "查看更多")]'
                ]
            )

            if html:
                recipes = await self.parse(html, url)
                all_recipes.extend(recipes)
                self.stats["items_scraped"] += len(recipes)

                # 可选: 保存到数据库
                if save_to_db:
                    for recipe in recipes:
                        self.save_to_db(recipe)

        self.end_stats()
        return all_recipes

    def save_to_db(self, recipe: Dict):
        """保存到数据库（示例）"""
        # TODO: 实现数据库保存逻辑
        # 可以用MongoDB、MySQL等
        pass

# 使用示例
async def main():
    # 加载代理池
    proxy_pool = ProxyPool.from_file("proxies.txt")

    # 创建爬虫实例
    crawler = MeishitianxiaCrawler(
        proxy_pool=proxy_pool,
        headless=True
    )

    # 使用async with自动管理浏览器
    async with crawler:
        # 执行爬取
        recipes = await crawler.run(
            category_urls=[
                "https://www.meishitianxia.com/chuancai/",
                "https://www.meishitianxia.com/yuecai/",
            ],
            max_recipes=50
        )

        # 保存结果
        import json
        with open("meishitianxia_recipes.json", "w", encoding="utf-8") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)

        print(f"成功爬取 {len(recipes)} 个菜谱")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 数据验证与清洗

### 使用DataValidator

```python
from gustobot.crawler.data_validator import DataValidator, RecipeModel

# 验证单个菜谱
recipe_data = {
    "name": "红烧肉",
    "ingredients": ["五花肉500g", "冰糖30g"],
    "steps": ["1. 切块", "2. 焯水", "3. 炖煮"]
}

validated = DataValidator.validate(recipe_data)
if validated:
    print(f"验证成功: {validated.name}")
    print(f"食材数量: {len(validated.ingredients)}")

# 批量验证
recipes = [recipe1, recipe2, recipe3]
valid_recipes = DataValidator.validate_batch(recipes)
print(f"有效菜谱: {len(valid_recipes)}/{len(recipes)}")

# 去重
unique_recipes = DataValidator.deduplicate(valid_recipes)
print(f"去重后: {len(unique_recipes)} 个菜谱")

# 时间规范化
minutes = DataValidator.normalize_time("1小时30分钟")  # 返回 90
minutes = DataValidator.normalize_time("PT1H30M")      # 返回 90
```

---

## 最佳实践

### 1. 合理设置请求延迟

```python
# ❌ 错误: 延迟太短，容易被封
crawler = BrowserCrawler(request_delay=(0.1, 0.5))

# ✅ 正确: 2-5秒随机延迟，模拟人类行为
crawler = BrowserCrawler(request_delay=(2, 5))

# ✅ 更保守: 对于严格的网站，使用更长延迟
crawler = BrowserCrawler(request_delay=(5, 10))
```

### 2. 使用代理池

```python
# ✅ 推荐: 使用代理池避免IP封禁
proxy_pool = ProxyPool.from_file("proxies.txt")
crawler = BrowserCrawler(proxy_pool=proxy_pool)
```

### 3. 遵守Robots.txt

```python
# ✅ 默认开启robots.txt检查
crawler = BaseCrawler(respect_robots_txt=True)  # 默认值

# ❌ 不推荐: 除非确实需要，否则不要禁用
crawler = BaseCrawler(respect_robots_txt=False)
```

### 4. 控制并发

```python
import asyncio

async def crawl_with_limit(urls, max_concurrent=3):
    """限制并发数量"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url):
        async with semaphore:
            return await crawler.fetch_page(url)

    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### 5. 错误处理

```python
from loguru import logger

async def safe_crawl(url):
    try:
        html = await crawler.fetch_page(url)
        if html:
            return await crawler.parse(html, url)
    except Exception as e:
        logger.error(f"爬取失败 {url}: {e}")
        return None
```

### 6. 使用上下文管理器

```python
# ✅ 推荐: 使用async with自动清理资源
async with BrowserCrawler() as crawler:
    recipes = await crawler.run(urls)

# ❌ 不推荐: 手动管理，容易忘记关闭
crawler = BrowserCrawler()
await crawler.init_browser()
recipes = await crawler.run(urls)
await crawler.close_browser()  # 可能忘记调用
```

---

## 常见问题

### Q1: 如何判断应该用HTTP爬虫还是浏览器爬虫？

**简单测试**:
1. 在浏览器中打开目标页面
2. 右键 -> "查看页面源代码"
3. 在源代码中搜索你想提取的内容

- ✅ **能找到** -> 用HTTP爬虫（BaseCrawler）
- ❌ **找不到** -> 用浏览器爬虫（BrowserCrawler）

### Q2: 爬虫一直返回空数据怎么办？

可能原因:
1. **网站需要JavaScript渲染** -> 改用BrowserCrawler
2. **选择器错误** -> 检查XPath/CSS选择器
3. **被反爬拦截** -> 检查响应内容，添加代理和延迟
4. **需要登录** -> 提供cookies参数

调试方法:
```python
# 保存HTML查看内容
html = await crawler.fetch_page(url)
with open("debug.html", "w", encoding="utf-8") as f:
    f.write(html)

# 或使用截图功能
await crawler.screenshot(url, "debug.png")
```

### Q3: 如何处理需要登录的网站？

```python
# 方法1: 提供Cookie
cookies = [
    {
        "name": "session_id",
        "value": "your_session_id",
        "domain": ".example.com",
        "path": "/"
    }
]

crawler = BrowserCrawler(cookies=cookies)

# 方法2: 在浏览器中手动登录后保存Cookie
# （建议先用headless=False手动登录一次）
```

### Q4: 爬虫速度太慢怎么办？

优化方法:
1. **减少延迟** (注意可能被封): `request_delay=(1, 2)`
2. **使用HTTP爬虫** 代替浏览器爬虫（如果可能）
3. **并发爬取** (控制好并发数)
4. **减少滚动次数**: `scroll_count=1`
5. **跳过不必要的等待**: 不设置`wait_selector`

### Q5: 如何处理分页？

```python
async def crawl_paginated_site(base_url, max_pages=10):
    recipes = []

    for page in range(1, max_pages + 1):
        # 构造分页URL
        url = f"{base_url}?page={page}"
        # 或: url = f"{base_url}&start={(page-1)*15}"

        html = await crawler.fetch_page(url)
        if html:
            page_recipes = await crawler.parse(html, url)
            recipes.extend(page_recipes)

            # 如果页面没有数据，说明到底了
            if not page_recipes:
                break

    return recipes
```

### Q6: 代理经常失效怎么办？

```python
# 启动代理池健康检查
import asyncio

proxy_pool = ProxyPool.from_file("proxies.txt")

# 后台持续健康检查
asyncio.create_task(proxy_pool.start_health_check_loop())

# 或定期手动检查
await proxy_pool.health_check()
```

---

## 相关文档

- [爬虫示例](crawler_examples.md) - 更多实战案例
- [反爬虫最佳实践](anti_scraping_guide.md) - 深入反爬技巧
- [gustobot/crawler/README.md](../app/crawler/README.md) - 模块文档

---

**祝你爬取顺利！** 🕷️

如有问题，请提交Issue: https://github.com/yourusername/GustoBot/issues

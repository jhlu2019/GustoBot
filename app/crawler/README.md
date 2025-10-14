# GustoBot 爬虫模块

企业级菜谱数据爬虫,支持多种数据源、代理池、反爬虫机制。

## 🌟 特性

- ✅ **多数据源支持**: Wikipedia、Schema.org标准网站、通用HTML
- ✅ **代理池管理**: 自动轮换、健康检查、失败重试
- ✅ **反爬虫机制**:
  - 随机User-Agent
  - 请求延迟
  - IP代理轮换
  - Robots.txt遵守
  - 重试机制
- ✅ **数据验证**: Pydantic模型验证、数据清洗、去重
- ✅ **Schema.org支持**: JSON-LD、Microdata格式解析
- ✅ **CLI工具**: 命令行界面方便使用
- ✅ **异步爬取**: 基于httpx的异步请求

## 📦 安装依赖

```bash
pip install httpx beautifulsoup4 fake-useragent pydantic
```

## 🚀 快速开始

### 1. Wikipedia菜谱爬取

```python
import asyncio
from app.crawler import WikipediaCrawler

async def main():
    crawler = WikipediaCrawler(language="zh")
    recipes = await crawler.run(
        search_queries=["川菜", "粤菜"],
        limit_per_query=5
    )
    print(f"爬取了 {len(recipes)} 个菜谱")

asyncio.run(main())
```

### 2. 通用网站爬取

```python
import asyncio
from app.crawler import RecipeCrawler

async def main():
    crawler = RecipeCrawler()
    recipes = await crawler.run([
        "https://example.com/recipe1",
        "https://example.com/recipe2"
    ])

asyncio.run(main())
```

### 3. 使用代理池

```python
from app.crawler import ProxyPool, RecipeCrawler

# 从文件加载代理
proxy_pool = ProxyPool.from_file("proxies.txt")

# 或手动添加代理
proxy_pool = ProxyPool()
proxy_pool.add_proxy(host="127.0.0.1", port=8080)
proxy_pool.add_proxy(
    host="proxy.example.com",
    port=8080,
    username="user",
    password="pass"
)

# 使用代理池
crawler = RecipeCrawler(proxy_pool=proxy_pool)
```

## 🔧 CLI 使用

### Wikipedia爬取

```bash
# 基础用法
python -m app.crawler.cli wikipedia --query "川菜" "粤菜"

# 指定语言和数量
python -m app.crawler.cli wikipedia --query "中国菜" --language zh --limit 10

# 使用代理
python -m app.crawler.cli wikipedia --query "烘焙" --proxy proxies.txt

# 保存到文件
python -m app.crawler.cli wikipedia --query "家常菜" --output recipes.json

# 直接导入到知识库
python -m app.crawler.cli wikipedia --query "甜品" --import-kb
```

### URL爬取

```bash
# 爬取指定URL
python -m app.crawler.cli urls --urls "https://example.com/recipe1" "https://example.com/recipe2"

# 使用代理并保存
python -m app.crawler.cli urls --urls "https://example.com/recipes" --proxy proxies.txt --output output.json

# 直接导入知识库
python -m app.crawler.cli urls --urls "https://example.com/recipe" --import-kb
```

### 从文件导入

```bash
# 将JSON文件导入知识库
python -m app.crawler.cli import --file recipes.json --batch-size 20
```

## 📝 代理配置

创建 `proxies.txt` 文件,每行一个代理:

```
# 格式1: host:port
127.0.0.1:8080

# 格式2: host:port:username:password
proxy.example.com:8080:user:pass

# 格式3: protocol://host:port
http://127.0.0.1:8080

# 格式4: protocol://username:password@host:port
http://user:pass@proxy.example.com:8080
```

## 🎯 高级用法

### 自定义爬虫

```python
from app.crawler import BaseCrawler
import httpx

class MyCrawler(BaseCrawler):
    def __init__(self, **kwargs):
        super().__init__(name="MyCrawler", **kwargs)

    async def parse(self, response: httpx.Response):
        # 实现解析逻辑
        pass

    async def run(self, **kwargs):
        # 实现爬取逻辑
        self.start_stats()

        response = await self.fetch("https://example.com")
        if response:
            recipes = await self.parse(response)

        self.end_stats()
        return recipes
```

### 代理池健康检查

```python
import asyncio
from app.crawler import ProxyPool

async def main():
    proxy_pool = ProxyPool.from_file("proxies.txt")

    # 手动健康检查
    await proxy_pool.health_check()

    # 启动自动健康检查(每5分钟)
    asyncio.create_task(proxy_pool.start_health_check_loop())

    # 查看统计
    stats = proxy_pool.get_stats()
    print(stats)

asyncio.run(main())
```

### 数据验证和清洗

```python
from app.crawler.data_validator import DataValidator, RecipeModel

# 验证单个菜谱
recipe_data = {
    "name": "红烧肉",
    "ingredients": ["五花肉500g", "冰糖30g"],
    "steps": ["1. 切块", "2. 焯水"]
}

validated = DataValidator.validate(recipe_data)
if validated:
    print(f"验证成功: {validated.name}")

# 批量验证
recipes = DataValidator.validate_batch(recipe_list)

# 去重
unique_recipes = DataValidator.deduplicate(recipes)

# 时间规范化
minutes = DataValidator.normalize_time("1小时30分钟")  # 返回 90
```

## 🛡️ 反爬虫最佳实践

### 1. 合理设置延迟

```python
crawler = RecipeCrawler(
    request_delay=(2, 5),  # 2-5秒随机延迟
    max_retries=3
)
```

### 2. 使用代理池

```python
proxy_pool = ProxyPool(
    check_interval=300,  # 5分钟健康检查
    max_fail_count=5     # 最大失败次数
)
```

### 3. 遵守Robots.txt

```python
crawler = RecipeCrawler(
    respect_robots_txt=True  # 默认开启
)
```

### 4. 控制并发

避免同时发起大量请求,使用异步但控制并发数:

```python
import asyncio

async def crawl_with_semaphore(urls, max_concurrent=3):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url):
        async with semaphore:
            return await crawler.fetch(url)

    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## 📊 数据格式

### 输出格式

```json
{
  "name": "红烧肉",
  "description": "经典中式菜肴,色泽红亮,肥而不腻",
  "category": "家常菜",
  "cuisine": "中国菜",
  "difficulty": "中等",
  "ingredients": [
    "五花肉500g",
    "冰糖30g",
    "生抽2勺",
    "老抽1勺"
  ],
  "steps": [
    "1. 五花肉切块,冷水下锅焯水",
    "2. 炒糖色,加入五花肉翻炒上色",
    "3. 加入调料和热水,小火炖煮40分钟"
  ],
  "time": {
    "prep": "PT15M",
    "cook": "PT45M",
    "total": "PT1H"
  },
  "servings": "4人份",
  "nutrition": {
    "calories": "450kcal",
    "protein": "20g",
    "carbs": "15g",
    "fat": "35g"
  },
  "tips": "糖色不要炒过头,容易发苦",
  "image": "https://example.com/image.jpg",
  "author": "Chef Zhang",
  "source": "Wikipedia",
  "url": "https://zh.wikipedia.org/wiki/红烧肉"
}
```

## ⚠️ 注意事项

1. **法律合规**: 仅爬取公开数据,遵守网站的robots.txt和服务条款
2. **请求频率**: 避免过高的请求频率,建议设置合理的延迟
3. **数据使用**: 爬取的数据仅用于个人学习或合法商业用途
4. **代理使用**: 使用合法的代理服务,不要使用非法代理
5. **错误处理**: 做好异常处理,避免爬虫异常退出

## 🔍 支持的网站类型

### ✅ 完全支持

- Wikipedia (多语言)
- 实现Schema.org Recipe标准的网站
- 包含JSON-LD结构化数据的网站
- 使用Microdata格式的网站

### ⚡ 部分支持

- 通用HTML结构的菜谱网站(使用启发式解析)
- 需要JavaScript渲染的网站(需配合Selenium使用)

### ❌ 不支持

- 需要登录的网站
- 有严格反爬措施的网站
- 动态加载内容的SPA应用(除非配合浏览器自动化)

## 📚 相关资源

- [Schema.org Recipe](https://schema.org/Recipe)
- [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page)
- [httpx Documentation](https://www.python-httpx.org/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进爬虫功能!

## 📄 许可证

Apache License 2.0

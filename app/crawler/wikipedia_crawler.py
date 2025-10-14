"""
维基百科菜谱爬虫
Wikipedia Recipe Crawler
"""
import httpx
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
from .base_crawler import BaseCrawler


class WikipediaCrawler(BaseCrawler):
    """维基百科菜谱爬虫"""

    def __init__(self, language: str = "zh", **kwargs):
        """
        初始化Wikipedia爬虫

        Args:
            language: 语言代码 (zh/en/etc)
            **kwargs: 传递给BaseCrawler的参数
        """
        super().__init__(name="WikipediaCrawler", **kwargs)
        self.language = language
        self.base_url = f"https://{language}.wikipedia.org"
        self.api_url = f"{self.base_url}/w/api.php"

    async def search_recipes(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索菜谱相关页面

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            页面列表
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet|titlesnippet"
        }

        data = await self.fetch_json(self.api_url, params=params, use_proxy=False)

        if not data or "query" not in data:
            return []

        results = []
        for item in data["query"].get("search", []):
            results.append({
                "title": item["title"],
                "page_id": item["pageid"],
                "snippet": item.get("snippet", "")
            })

        logger.info(f"Found {len(results)} pages for query: {query}")
        return results

    async def get_page_content(self, page_title: str) -> Optional[Dict]:
        """
        获取页面完整内容

        Args:
            page_title: 页面标题

        Returns:
            页面内容字典
        """
        params = {
            "action": "parse",
            "format": "json",
            "page": page_title,
            "prop": "text|categories|sections",
            "disableeditsection": 1
        }

        data = await self.fetch_json(self.api_url, params=params, use_proxy=False)

        if not data or "parse" not in data:
            return None

        parse_data = data["parse"]
        return {
            "title": parse_data["title"],
            "page_id": parse_data["pageid"],
            "html": parse_data["text"]["*"],
            "categories": [cat["*"] for cat in parse_data.get("categories", [])],
            "sections": parse_data.get("sections", [])
        }

    async def parse(self, response: httpx.Response) -> List[Dict]:
        """
        解析维基百科页面

        Args:
            response: HTTP响应

        Returns:
            解析后的菜谱数据
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        recipes = []

        # 提取标题
        title_elem = soup.find('h1', class_='firstHeading')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"

        # 提取信息框数据
        infobox = soup.find('table', class_='infobox')
        recipe_data = {
            "name": title,
            "source": "Wikipedia",
            "url": response.url,
            "category": "",
            "cuisine": "",
            "ingredients": [],
            "steps": [],
            "description": ""
        }

        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)

                    if '类型' in key or 'Type' in key:
                        recipe_data["category"] = value
                    elif '菜系' in key or 'Cuisine' in key:
                        recipe_data["cuisine"] = value

        # 提取段落内容
        content_div = soup.find('div', class_='mw-parser-output')
        if content_div:
            # 提取简介
            paragraphs = content_div.find_all('p', recursive=False)
            descriptions = []
            for p in paragraphs[:3]:  # 前3段作为描述
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    descriptions.append(text)
            recipe_data["description"] = "\n\n".join(descriptions)

            # 提取成分/材料
            for heading in content_div.find_all(['h2', 'h3']):
                heading_text = heading.get_text(strip=True)

                if any(keyword in heading_text for keyword in ['材料', '食材', 'Ingredients', '成分']):
                    next_elem = heading.find_next_sibling()
                    if next_elem and next_elem.name == 'ul':
                        for li in next_elem.find_all('li', recursive=False):
                            ingredient = li.get_text(strip=True)
                            if ingredient:
                                recipe_data["ingredients"].append(ingredient)

                elif any(keyword in heading_text for keyword in ['做法', '步骤', 'Preparation', 'Method', 'Steps']):
                    next_elem = heading.find_next_sibling()
                    if next_elem and next_elem.name == 'ol':
                        for i, li in enumerate(next_elem.find_all('li', recursive=False), 1):
                            step = li.get_text(strip=True)
                            if step:
                                recipe_data["steps"].append(f"{i}. {step}")

        recipes.append(recipe_data)
        self.stats["items_scraped"] += 1

        return recipes

    async def parse_html_content(self, html: str, page_title: str, page_url: str) -> Dict:
        """
        解析HTML内容

        Args:
            html: HTML内容
            page_title: 页面标题
            page_url: 页面URL

        Returns:
            解析后的菜谱数据
        """
        soup = BeautifulSoup(html, 'html.parser')

        recipe_data = {
            "name": page_title,
            "source": "Wikipedia",
            "url": page_url,
            "category": "",
            "cuisine": "",
            "ingredients": [],
            "steps": [],
            "description": "",
            "nutrition": {}
        }

        # 提取所有段落作为描述
        paragraphs = soup.find_all('p', recursive=False)
        descriptions = []
        for p in paragraphs[:2]:
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                descriptions.append(text)
        recipe_data["description"] = "\n\n".join(descriptions)

        # 提取列表内容
        for ul in soup.find_all('ul'):
            # 尝试识别是否为食材列表
            items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
            if items and len(items) > 0:
                # 简单启发式: 如果列表项包含数字或量词,可能是食材
                if any(any(char.isdigit() for char in item) for item in items[:3]):
                    recipe_data["ingredients"].extend(items)

        # 提取有序列表作为步骤
        for ol in soup.find_all('ol'):
            steps = [li.get_text(strip=True) for li in ol.find_all('li', recursive=False)]
            if steps:
                recipe_data["steps"].extend([f"{i+1}. {step}" for i, step in enumerate(steps)])

        self.stats["items_scraped"] += 1
        return recipe_data

    async def crawl_recipe(self, page_title: str) -> Optional[Dict]:
        """
        爬取单个菜谱页面

        Args:
            page_title: 页面标题

        Returns:
            菜谱数据
        """
        logger.info(f"Crawling recipe: {page_title}")

        # 先检查robots.txt
        await self.check_robots_txt(self.base_url)

        # 获取页面内容
        page_data = await self.get_page_content(page_title)
        if not page_data:
            logger.error(f"Failed to get page content for: {page_title}")
            return None

        # 解析HTML
        page_url = f"{self.base_url}/wiki/{page_title.replace(' ', '_')}"
        recipe = await self.parse_html_content(
            html=page_data["html"],
            page_title=page_data["title"],
            page_url=page_url
        )

        return recipe

    async def run(
        self,
        search_queries: Optional[List[str]] = None,
        page_titles: Optional[List[str]] = None,
        limit_per_query: int = 5
    ) -> List[Dict]:
        """
        运行爬虫

        Args:
            search_queries: 搜索关键词列表
            page_titles: 直接指定的页面标题列表
            limit_per_query: 每个查询的结果数量

        Returns:
            爬取的菜谱列表
        """
        self.start_stats()

        all_recipes = []

        try:
            # 处理搜索查询
            if search_queries:
                for query in search_queries:
                    logger.info(f"Searching for: {query}")
                    results = await self.search_recipes(query, limit=limit_per_query)

                    for result in results:
                        recipe = await self.crawl_recipe(result["title"])
                        if recipe:
                            all_recipes.append(recipe)

            # 处理直接指定的页面
            if page_titles:
                for title in page_titles:
                    recipe = await self.crawl_recipe(title)
                    if recipe:
                        all_recipes.append(recipe)

            logger.info(f"Successfully crawled {len(all_recipes)} recipes")

        except Exception as e:
            logger.error(f"Error during crawling: {e}")

        finally:
            self.end_stats()

        return all_recipes

    @classmethod
    async def quick_search(
        cls,
        query: str,
        language: str = "zh",
        limit: int = 5
    ) -> List[Dict]:
        """
        快速搜索和爬取菜谱

        Args:
            query: 搜索关键词
            language: 语言代码
            limit: 结果数量

        Returns:
            菜谱列表
        """
        crawler = cls(language=language)
        return await crawler.run(search_queries=[query], limit_per_query=limit)

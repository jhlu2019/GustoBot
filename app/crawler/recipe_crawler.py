"""
通用菜谱网站爬虫
Generic Recipe Site Crawler with Schema.org support
"""
import httpx
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
from .base_crawler import BaseCrawler


class RecipeCrawler(BaseCrawler):
    """通用菜谱网站爬虫,支持Schema.org标准"""

    def __init__(self, **kwargs):
        """初始化通用菜谱爬虫"""
        super().__init__(name="RecipeCrawler", **kwargs)

    async def parse(self, response: httpx.Response) -> List[Dict]:
        """
        解析页面内容

        支持以下格式:
        1. Schema.org/Recipe (JSON-LD)
        2. Microdata
        3. 通用HTML结构

        Args:
            response: HTTP响应

        Returns:
            解析后的菜谱列表
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        recipes = []

        # 方法1: 尝试解析JSON-LD (Schema.org)
        json_ld_recipes = self._parse_json_ld(soup)
        if json_ld_recipes:
            recipes.extend(json_ld_recipes)
            logger.info(f"Found {len(json_ld_recipes)} recipes from JSON-LD")

        # 方法2: 尝试解析Microdata
        if not recipes:
            microdata_recipes = self._parse_microdata(soup)
            if microdata_recipes:
                recipes.extend(microdata_recipes)
                logger.info(f"Found {len(microdata_recipes)} recipes from Microdata")

        # 方法3: 通用HTML解析
        if not recipes:
            html_recipe = self._parse_html(soup, str(response.url))
            if html_recipe:
                recipes.append(html_recipe)
                logger.info("Parsed recipe from HTML structure")

        self.stats["items_scraped"] += len(recipes)
        return recipes

    def _parse_json_ld(self, soup: BeautifulSoup) -> List[Dict]:
        """
        解析JSON-LD格式的Recipe数据

        Args:
            soup: BeautifulSoup对象

        Returns:
            菜谱列表
        """
        recipes = []

        # 查找所有JSON-LD脚本
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)

                # 处理单个Recipe或Recipe数组
                if isinstance(data, dict):
                    if data.get('@type') == 'Recipe':
                        recipe = self._normalize_recipe_schema(data)
                        recipes.append(recipe)
                    elif data.get('@graph'):
                        # 有些网站使用@graph包装
                        for item in data['@graph']:
                            if isinstance(item, dict) and item.get('@type') == 'Recipe':
                                recipe = self._normalize_recipe_schema(item)
                                recipes.append(recipe)

                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Recipe':
                            recipe = self._normalize_recipe_schema(item)
                            recipes.append(recipe)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")
            except Exception as e:
                logger.error(f"Error parsing JSON-LD: {e}")

        return recipes

    def _normalize_recipe_schema(self, data: Dict) -> Dict:
        """
        规范化Schema.org Recipe数据

        Args:
            data: Schema.org Recipe对象

        Returns:
            规范化的菜谱字典
        """
        recipe = {
            "name": data.get('name', ''),
            "description": data.get('description', ''),
            "category": data.get('recipeCategory', ''),
            "cuisine": data.get('recipeCuisine', ''),
            "ingredients": [],
            "steps": [],
            "time": {},
            "nutrition": {},
            "image": '',
            "author": '',
            "source": "Schema.org",
            "url": data.get('url', '')
        }

        # 食材
        ingredients = data.get('recipeIngredient', [])
        if isinstance(ingredients, list):
            recipe["ingredients"] = ingredients
        elif isinstance(ingredients, str):
            recipe["ingredients"] = [ingredients]

        # 步骤
        instructions = data.get('recipeInstructions', [])
        if isinstance(instructions, list):
            for i, instruction in enumerate(instructions, 1):
                if isinstance(instruction, str):
                    recipe["steps"].append(f"{i}. {instruction}")
                elif isinstance(instruction, dict):
                    text = instruction.get('text', instruction.get('name', ''))
                    if text:
                        recipe["steps"].append(f"{i}. {text}")
        elif isinstance(instructions, str):
            # 如果是单个字符串,按行分割
            lines = [line.strip() for line in instructions.split('\n') if line.strip()]
            recipe["steps"] = [f"{i}. {line}" for i, line in enumerate(lines, 1)]

        # 时间信息
        if 'prepTime' in data:
            recipe["time"]["prep"] = data['prepTime']
        if 'cookTime' in data:
            recipe["time"]["cook"] = data['cookTime']
        if 'totalTime' in data:
            recipe["time"]["total"] = data['totalTime']

        # 营养信息
        if 'nutrition' in data and isinstance(data['nutrition'], dict):
            nutrition = data['nutrition']
            recipe["nutrition"] = {
                "calories": nutrition.get('calories', ''),
                "protein": nutrition.get('proteinContent', ''),
                "carbs": nutrition.get('carbohydrateContent', ''),
                "fat": nutrition.get('fatContent', '')
            }

        # 图片
        if 'image' in data:
            image = data['image']
            if isinstance(image, str):
                recipe["image"] = image
            elif isinstance(image, dict):
                recipe["image"] = image.get('url', '')
            elif isinstance(image, list) and image:
                recipe["image"] = image[0] if isinstance(image[0], str) else image[0].get('url', '')

        # 作者
        if 'author' in data:
            author = data['author']
            if isinstance(author, str):
                recipe["author"] = author
            elif isinstance(author, dict):
                recipe["author"] = author.get('name', '')

        # 其他有用字段
        if 'aggregateRating' in data:
            rating = data['aggregateRating']
            if isinstance(rating, dict):
                recipe["rating"] = {
                    "value": rating.get('ratingValue', ''),
                    "count": rating.get('ratingCount', '')
                }

        if 'recipeYield' in data:
            recipe["servings"] = data['recipeYield']

        return recipe

    def _parse_microdata(self, soup: BeautifulSoup) -> List[Dict]:
        """
        解析Microdata格式的Recipe数据

        Args:
            soup: BeautifulSoup对象

        Returns:
            菜谱列表
        """
        recipes = []

        # 查找所有带有itemtype="https://schema.org/Recipe"的元素
        for recipe_elem in soup.find_all(attrs={'itemtype': lambda x: x and 'Recipe' in x}):
            try:
                recipe = {
                    "name": "",
                    "description": "",
                    "ingredients": [],
                    "steps": [],
                    "source": "Microdata"
                }

                # 提取名称
                name_elem = recipe_elem.find(attrs={'itemprop': 'name'})
                if name_elem:
                    recipe["name"] = name_elem.get_text(strip=True)

                # 提取描述
                desc_elem = recipe_elem.find(attrs={'itemprop': 'description'})
                if desc_elem:
                    recipe["description"] = desc_elem.get_text(strip=True)

                # 提取食材
                for ingredient_elem in recipe_elem.find_all(attrs={'itemprop': 'recipeIngredient'}):
                    ingredient = ingredient_elem.get_text(strip=True)
                    if ingredient:
                        recipe["ingredients"].append(ingredient)

                # 提取步骤
                for instruction_elem in recipe_elem.find_all(attrs={'itemprop': 'recipeInstructions'}):
                    step = instruction_elem.get_text(strip=True)
                    if step:
                        recipe["steps"].append(step)

                if recipe["name"]:
                    recipes.append(recipe)

            except Exception as e:
                logger.error(f"Error parsing Microdata: {e}")

        return recipes

    def _parse_html(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """
        通用HTML解析(启发式方法)

        Args:
            soup: BeautifulSoup对象
            url: 页面URL

        Returns:
            菜谱字典或None
        """
        recipe = {
            "name": "",
            "description": "",
            "ingredients": [],
            "steps": [],
            "source": "HTML",
            "url": url
        }

        # 提取标题
        title = soup.find('h1')
        if title:
            recipe["name"] = title.get_text(strip=True)
        else:
            recipe["name"] = soup.title.get_text(strip=True) if soup.title else "Unknown"

        # 提取描述(取前几个段落)
        paragraphs = soup.find_all('p')
        descriptions = []
        for p in paragraphs[:3]:
            text = p.get_text(strip=True)
            if text and len(text) > 30:
                descriptions.append(text)
        recipe["description"] = "\n\n".join(descriptions)

        # 启发式查找食材列表
        # 常见关键词: 食材、材料、ingredients, materials
        ingredient_keywords = ['食材', '材料', 'ingredients', 'materials', '用料']
        for keyword in ingredient_keywords:
            # 查找包含关键词的标题
            heading = soup.find(['h2', 'h3', 'h4'], string=lambda text: text and keyword.lower() in text.lower())
            if heading:
                # 查找后续的列表
                next_elem = heading.find_next_sibling()
                while next_elem:
                    if next_elem.name == 'ul':
                        for li in next_elem.find_all('li'):
                            ingredient = li.get_text(strip=True)
                            if ingredient:
                                recipe["ingredients"].append(ingredient)
                        break
                    elif next_elem.name in ['h2', 'h3', 'h4']:
                        break
                    next_elem = next_elem.find_next_sibling()

        # 启发式查找步骤列表
        # 常见关键词: 步骤、做法、制作、instructions, directions, method
        step_keywords = ['步骤', '做法', '制作', 'instructions', 'directions', 'method', '烹饪']
        for keyword in step_keywords:
            heading = soup.find(['h2', 'h3', 'h4'], string=lambda text: text and keyword.lower() in text.lower())
            if heading:
                next_elem = heading.find_next_sibling()
                while next_elem:
                    if next_elem.name == 'ol':
                        for i, li in enumerate(next_elem.find_all('li'), 1):
                            step = li.get_text(strip=True)
                            if step:
                                recipe["steps"].append(f"{i}. {step}")
                        break
                    elif next_elem.name in ['h2', 'h3', 'h4']:
                        break
                    next_elem = next_elem.find_next_sibling()

        # 如果找到了有效数据,返回
        if recipe["name"] and (recipe["ingredients"] or recipe["steps"]):
            return recipe

        return None

    async def crawl_url(self, url: str) -> Optional[List[Dict]]:
        """
        爬取单个URL

        Args:
            url: 目标URL

        Returns:
            菜谱列表
        """
        logger.info(f"Crawling URL: {url}")

        response = await self.fetch(url)
        if response:
            return await self.parse(response)

        return None

    async def run(self, urls: List[str]) -> List[Dict]:
        """
        运行爬虫

        Args:
            urls: URL列表

        Returns:
            爬取的菜谱列表
        """
        self.start_stats()

        all_recipes = []

        try:
            for url in urls:
                recipes = await self.crawl_url(url)
                if recipes:
                    all_recipes.extend(recipes)

            logger.info(f"Successfully crawled {len(all_recipes)} recipes from {len(urls)} URLs")

        except Exception as e:
            logger.error(f"Error during crawling: {e}")

        finally:
            self.end_stats()

        return all_recipes

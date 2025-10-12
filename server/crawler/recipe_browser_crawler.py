"""
基于浏览器的菜谱爬虫示例
Recipe Browser Crawler Example
展示如何使用BrowserCrawler基类进行扩展
"""
from typing import List, Dict, Optional
from lxml import etree
from loguru import logger
from .browser_crawler import BrowserCrawler
from .data_validator import DataValidator, RecipeModel


class RecipeBrowserCrawler(BrowserCrawler):
    """
    菜谱浏览器爬虫
    适用于需要JavaScript渲染的菜谱网站
    """

    def __init__(
        self,
        site_name: str = "Generic Recipe Site",
        **kwargs
    ):
        """
        初始化菜谱浏览器爬虫

        Args:
            site_name: 网站名称
            **kwargs: 传递给BrowserCrawler的参数
        """
        super().__init__(name=f"RecipeBrowserCrawler-{site_name}", **kwargs)
        self.site_name = site_name

    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """
        解析菜谱页面内容

        Args:
            html_content: HTML内容
            url: 页面URL

        Returns:
            菜谱数据列表
        """
        html_tree = etree.HTML(html_content)
        recipes = []

        try:
            recipe_data = {
                "name": "",
                "description": "",
                "ingredients": [],
                "steps": [],
                "source": self.site_name,
                "url": url
            }

            # 提取标题
            title_nodes = html_tree.xpath("//h1//text()")
            if title_nodes:
                recipe_data["name"] = " ".join([t.strip() for t in title_nodes if t.strip()])

            # 提取描述
            desc_nodes = html_tree.xpath("//meta[@name='description']/@content")
            if desc_nodes:
                recipe_data["description"] = desc_nodes[0].strip()
            else:
                # 备用: 提取前几个段落
                para_nodes = html_tree.xpath("//p//text()")
                descriptions = [p.strip() for p in para_nodes if p.strip() and len(p.strip()) > 20]
                if descriptions:
                    recipe_data["description"] = "\n".join(descriptions[:2])

            # 提取食材 (通用启发式)
            ingredient_keywords = ['食材', '材料', 'ingredients', 'materials', '用料']
            for keyword in ingredient_keywords:
                heading = html_tree.xpath(
                    f"//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')] | "
                    f"//h3[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')] | "
                    f"//div[contains(@class, 'ingredient')]//li"
                )
                if heading:
                    for elem in heading:
                        # 查找后续的列表
                        next_ul = elem.xpath("following-sibling::ul[1]//li//text()")
                        if next_ul:
                            recipe_data["ingredients"].extend([i.strip() for i in next_ul if i.strip()])
                            break

            # 如果没找到,尝试直接找所有列表项
            if not recipe_data["ingredients"]:
                all_lis = html_tree.xpath("//ul//li//text()")
                potential_ingredients = [li.strip() for li in all_lis if li.strip() and len(li.strip()) < 100]
                if potential_ingredients:
                    recipe_data["ingredients"] = potential_ingredients[:20]  # 限制数量

            # 提取步骤
            step_keywords = ['步骤', '做法', '制作', 'instructions', 'directions', 'method']
            for keyword in step_keywords:
                heading = html_tree.xpath(
                    f"//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')] | "
                    f"//h3[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')] | "
                    f"//div[contains(@class, 'step')]"
                )
                if heading:
                    for elem in heading:
                        next_ol = elem.xpath("following-sibling::ol[1]//li//text()")
                        if next_ol:
                            recipe_data["steps"] = [f"{i+1}. {step.strip()}" for i, step in enumerate(next_ol) if step.strip()]
                            break

            # 如果步骤为空,尝试有序列表
            if not recipe_data["steps"]:
                steps_ol = html_tree.xpath("//ol//li//text()")
                if steps_ol:
                    recipe_data["steps"] = [f"{i+1}. {step.strip()}" for i, step in enumerate(steps_ol) if step.strip()]

            if recipe_data["name"]:
                recipes.append(recipe_data)
                self.stats["items_scraped"] += 1

        except Exception as e:
            logger.error(f"Error parsing recipe from {url}: {e}")

        return recipes

    async def crawl_recipe_page(
        self,
        url: str,
        wait_selector: Optional[str] = "body",
        scroll_count: int = 3,
        click_expand: bool = False
    ) -> Optional[List[Dict]]:
        """
        爬取单个菜谱页面

        Args:
            url: 菜谱URL
            wait_selector: 等待的选择器
            scroll_count: 滚动次数
            click_expand: 是否点击展开按钮

        Returns:
            菜谱数据列表
        """
        logger.info(f"Crawling recipe page: {url}")

        # 构建点击选择器列表
        click_selectors = None
        if click_expand:
            click_selectors = [
                '//*[contains(text(), "展开")]',
                '//*[contains(text(), "查看更多")]',
                '//*[contains(text(), "Show more")]',
                '//button[contains(@class, "expand")]'
            ]

        html_content = await self.fetch_page(
            url=url,
            wait_selector=wait_selector,
            scroll_count=scroll_count,
            click_selectors=click_selectors
        )

        if html_content:
            return await self.parse(html_content, url)

        return None

    async def crawl_list_page(
        self,
        url: str,
        link_xpath: str = "//a[contains(@href, 'recipe')]/@href",
        base_url: Optional[str] = None
    ) -> List[str]:
        """
        爬取列表页,提取菜谱链接

        Args:
            url: 列表页URL
            link_xpath: 提取链接的XPath
            base_url: 基础URL(用于拼接相对路径)

        Returns:
            菜谱URL列表
        """
        logger.info(f"Crawling list page: {url}")

        html_content = await self.fetch_page(
            url=url,
            scroll_count=3  # 滚动以加载更多内容
        )

        if not html_content:
            return []

        html_tree = etree.HTML(html_content)
        links = html_tree.xpath(link_xpath)

        # 处理相对路径
        if base_url:
            links = [
                link if link.startswith('http') else f"{base_url.rstrip('/')}/{link.lstrip('/')}"
                for link in links
            ]

        # 去重
        unique_links = list(set(links))
        logger.info(f"Found {len(unique_links)} unique recipe links")

        return unique_links

    async def run(
        self,
        urls: Optional[List[str]] = None,
        list_pages: Optional[List[str]] = None,
        link_xpath: str = "//a[contains(@href, 'recipe')]/@href",
        save_to_file: Optional[str] = None
    ) -> List[Dict]:
        """
        运行爬虫

        Args:
            urls: 直接指定的菜谱URL列表
            list_pages: 列表页URL(用于提取菜谱链接)
            link_xpath: 提取链接的XPath
            save_to_file: 保存链接到文件

        Returns:
            爬取的菜谱列表
        """
        self.start_stats()

        all_recipes = []
        recipe_urls = urls or []

        try:
            # 从列表页提取链接
            if list_pages:
                for list_url in list_pages:
                    links = await self.crawl_list_page(list_url, link_xpath)
                    recipe_urls.extend(links)

            # 保存链接到文件
            if save_to_file and recipe_urls:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    for url in recipe_urls:
                        f.write(url + '\n')
                logger.info(f"Saved {len(recipe_urls)} URLs to {save_to_file}")

            # 爬取每个菜谱页面
            for url in recipe_urls:
                recipes = await self.crawl_recipe_page(url)
                if recipes:
                    all_recipes.extend(recipes)

            logger.info(f"Successfully crawled {len(all_recipes)} recipes")

        except Exception as e:
            logger.error(f"Error during crawling: {e}")

        finally:
            self.end_stats()

        return all_recipes


class DoubanRecipeCrawler(BrowserCrawler):
    """
    豆瓣风格的爬虫示例
    模仿您提供的代码结构
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        mongo_db: str = "recipe_database",
        mongo_collection: str = "recipes",
        **kwargs
    ):
        """
        初始化豆瓣风格爬虫

        Args:
            mongo_uri: MongoDB连接URI
            mongo_db: 数据库名
            mongo_collection: 集合名
            **kwargs: 传递给BrowserCrawler的参数
        """
        super().__init__(name="DoubanRecipeCrawler", **kwargs)

        # MongoDB配置
        from pymongo import MongoClient
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]
        self.collection = self.db[mongo_collection]

    async def get_root_urls(self, base_url: str, max_pages: int = 5) -> List[str]:
        """
        构造分页URL列表

        Args:
            base_url: 基础URL
            max_pages: 最大页数

        Returns:
            分页URL列表
        """
        root_urls = [f"{base_url}&start={i * 15}" for i in range(max_pages)]
        return root_urls

    async def parse_list_page(self, html_content: str, url: str) -> List[str]:
        """
        解析列表页,提取详情页链接

        Args:
            html_content: HTML内容
            url: 页面URL

        Returns:
            详情页URL列表
        """
        html_tree = etree.HTML(html_content)

        # 根据实际页面结构调整XPath
        links = html_tree.xpath('//*[@id="root"]//div/div/div/div[1]/a/@href')

        # 去重
        unique_links = list(set(links))
        logger.info(f"Parsed {len(unique_links)} recipe links from list page")

        return unique_links

    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """
        解析详情页内容

        Args:
            html_content: HTML内容
            url: 页面URL

        Returns:
            菜谱数据列表
        """
        html_tree = etree.HTML(html_content)

        try:
            # 提取标题
            title_raw = html_tree.xpath("//h1//text()")
            title = [t.strip() for t in title_raw if t.strip()]

            # 提取详细信息
            info_raw = html_tree.xpath('string(//*[@id="info"])')
            info = ' '.join(info_raw.split())

            # 提取评分
            rating = html_tree.xpath('//*[@id="interest_sectl"]/div/div[2]/strong/text()')

            # 提取内容
            content = html_tree.xpath('//*[@id="link-report"]/div/div//text()')
            content_cleaned = ''.join(content).strip()

            # 提取图片
            imgs = html_tree.xpath('//div[@id="mainpic"]//img/@src')

            recipe_data = {
                "title": title[0].strip() if title else "未知标题",
                "info": info,
                "rating": rating[0].strip() if rating else "无评分",
                "content": content_cleaned if content else "无",
                "image": imgs[0] if imgs else "",
                "url": url,
                "source": "Douban-like"
            }

            self.stats["items_scraped"] += 1
            return [recipe_data]

        except Exception as e:
            logger.error(f"Error parsing detail page {url}: {e}")
            return []

    def save_to_mongo(self, data: Dict):
        """
        保存数据到MongoDB

        Args:
            data: 菜谱数据
        """
        try:
            # 检查是否已存在
            if not self.collection.find_one({"url": data["url"]}):
                self.collection.insert_one(data)
                logger.info(f"成功保存到MongoDB: {data.get('title', '无标题')}")
            else:
                logger.info(f"数据已存在,跳过: {data.get('title', '无标题')}")
        except Exception as e:
            logger.error(f"保存到MongoDB失败: {e}")

    async def save_urls_to_file(self, urls: List[str], output_file: str):
        """
        保存URL列表到文件

        Args:
            urls: URL列表
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(url + '\n')
            logger.info(f"保存 {len(urls)} 个URL到 {output_file}")
        except Exception as e:
            logger.error(f"保存URL文件失败: {e}")

    async def load_urls_from_file(self, input_file: str) -> List[str]:
        """
        从文件加载URL列表

        Args:
            input_file: 输入文件路径

        Returns:
            URL列表
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"从 {input_file} 读取到 {len(urls)} 个URL")
            return urls
        except Exception as e:
            logger.error(f"读取URL文件失败: {e}")
            return []

    async def run(
        self,
        base_url: Optional[str] = None,
        max_pages: int = 5,
        urls_file: Optional[str] = None,
        save_urls: Optional[str] = None
    ) -> List[Dict]:
        """
        运行爬虫

        Args:
            base_url: 搜索基础URL
            max_pages: 最大页数
            urls_file: URL文件路径(优先级高)
            save_urls: 保存URL到文件

        Returns:
            爬取的菜谱列表
        """
        self.start_stats()

        all_recipes = []
        recipe_urls = []

        try:
            # 阶段1: 获取URL列表
            if urls_file:
                # 从文件加载
                recipe_urls = await self.load_urls_from_file(urls_file)
            elif base_url:
                # 从列表页爬取
                root_urls = await self.get_root_urls(base_url, max_pages)

                for root_url in root_urls:
                    logger.info(f"正在爬取列表页: {root_url}")

                    html_content = await self.fetch_page(
                        url=root_url,
                        wait_selector='#root div div div div a',
                        scroll_count=3
                    )

                    if html_content:
                        page_urls = await self.parse_list_page(html_content, root_url)
                        recipe_urls.extend(page_urls)

                # 去重
                recipe_urls = list(set(recipe_urls))
                logger.info(f"共获取 {len(recipe_urls)} 个唯一菜谱链接")

                # 保存URL
                if save_urls:
                    await self.save_urls_to_file(recipe_urls, save_urls)

            # 阶段2: 爬取详情页
            for url in recipe_urls:
                # 检查是否已存在
                if self.collection.find_one({"url": url}):
                    logger.info(f"URL已存在于MongoDB,跳过: {url}")
                    continue

                logger.info(f"正在爬取详情页: {url}")

                html_content = await self.fetch_page(
                    url=url,
                    wait_selector="body",
                    scroll_count=2
                )

                if html_content:
                    recipes = await self.parse(html_content, url)

                    for recipe in recipes:
                        all_recipes.append(recipe)
                        self.save_to_mongo(recipe)

            logger.info(f"成功爬取 {len(all_recipes)} 个菜谱")

        except Exception as e:
            logger.error(f"爬虫运行失败: {e}")

        finally:
            self.end_stats()
            self.client.close()

        return all_recipes


# 使用示例
async def example_usage():
    """使用示例"""
    from .proxy_pool import ProxyPool

    # 示例1: 简单的菜谱爬虫
    async with RecipeBrowserCrawler(
        headless=True,
        request_delay=(2, 5)
    ) as crawler:
        recipes = await crawler.run(
            urls=["https://example.com/recipe1", "https://example.com/recipe2"]
        )
        print(f"爬取了 {len(recipes)} 个菜谱")

    # 示例2: 使用代理池
    proxy_pool = ProxyPool.from_file("proxies.txt")

    async with RecipeBrowserCrawler(
        proxy_pool=proxy_pool,
        headless=True
    ) as crawler:
        recipes = await crawler.run(
            list_pages=["https://example.com/recipes?page=1"],
            link_xpath="//a[@class='recipe-link']/@href"
        )

    # 示例3: 豆瓣风格爬虫
    crawler = DoubanRecipeCrawler(
        mongo_uri="mongodb://localhost:27017/",
        mongo_db="recipe_db",
        mongo_collection="recipes",
        headless=False,  # 调试时可见浏览器
        request_delay=(3, 6)
    )

    await crawler.init_browser()

    recipes = await crawler.run(
        base_url="https://example.com/search?q=recipe",
        max_pages=5,
        save_urls="recipe_urls.txt"
    )

    await crawler.close_browser()

    print(f"总共爬取了 {len(recipes)} 个菜谱")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

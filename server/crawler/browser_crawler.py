"""
浏览器自动化爬虫基类
Browser-Based Crawler with Playwright
支持动态页面、JavaScript渲染内容

本模块提供基于Playwright的浏览器自动化爬虫基类,适用于需要JavaScript渲染的动态页面。
相比于简单的HTTP请求,浏览器爬虫可以:
  - 渲染JavaScript动态内容
  - 模拟用户操作(滚动、点击等)
  - 处理需要登录的页面
  - 执行复杂的页面交互

使用场景:
  - SPA单页应用
  - 需要下拉加载更多的页面
  - 需要点击"展开"按钮才能看到完整内容的页面
  - 需要等待AJAX请求完成的页面

示例:
    from server.crawler.browser_crawler import BrowserCrawler

    class MyRecipeCrawler(BrowserCrawler):
        async def parse(self, html_content: str, url: str):
            # 解析HTML内容
            pass

        async def run(self):
            # 爬取逻辑
            html = await self.fetch_page(
                "https://example.com/recipe",
                scroll_count=3,  # 滚动3次触发懒加载
                click_selectors=['//button[contains(text(), "展开")]']  # 点击展开按钮
            )
            return await self.parse(html, url)
"""
import asyncio
import random
import time
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger
from .proxy_pool import ProxyPool
from datetime import datetime


class BrowserCrawler(ABC):
    """
    基于Playwright的浏览器自动化爬虫基类
    适用于需要JavaScript渲染的动态页面
    """

    # User-Agent池
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0',
    ]

    def __init__(
        self,
        name: str,
        proxy_pool: Optional[ProxyPool] = None,
        headless: bool = True,
        use_random_ua: bool = True,
        request_delay: tuple = (2, 5),
        max_retries: int = 3,
        timeout: int = 60000,
        viewport: Dict = None,
        cookies: Optional[List[Dict]] = None,
        extra_headers: Optional[Dict] = None
    ):
        """
        初始化浏览器爬虫

        Args:
            name: 爬虫名称
            proxy_pool: 代理池
            headless: 是否无头模式
            use_random_ua: 是否使用随机User-Agent
            request_delay: 请求延迟范围(秒)
            max_retries: 最大重试次数
            timeout: 页面加载超时时间(毫秒)
            viewport: 视口大小 {"width": 1920, "height": 1080}
            cookies: Cookie列表
            extra_headers: 额外的请求头
        """
        self.name = name
        self.proxy_pool = proxy_pool
        self.headless = headless
        self.use_random_ua = use_random_ua
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.cookies = cookies or []
        self.extra_headers = extra_headers or {}

        # Playwright实例
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        # 统计信息
        self.stats = {
            "pages_loaded": 0,
            "pages_failed": 0,
            "items_scraped": 0,
            "start_time": None,
            "end_time": None
        }

        logger.info(f"BrowserCrawler '{self.name}' initialized")

    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        if self.use_random_ua:
            return random.choice(self.USER_AGENTS)
        return self.USER_AGENTS[0]

    async def init_browser(self):
        """
        初始化浏览器实例

        该方法会:
        1. 启动Playwright
        2. 配置代理(如果提供)
        3. 启动Chromium浏览器
        4. 创建浏览器上下文(设置视口、User-Agent、请求头等)
        5. 注入Cookie(如果提供)

        注意:
        - 浏览器上下文(BrowserContext)是独立的会话,有自己的Cookie、存储等
        - 同一个浏览器可以创建多个上下文,实现多账号爬取
        - 代理配置格式: {"server": "http://ip:port", "username": "...", "password": "..."}
        """
        if self.browser:
            logger.warning("Browser already initialized")
            return

        try:
            # 启动Playwright
            self.playwright = await async_playwright().start()

            # 配置代理
            proxy_config = None
            if self.proxy_pool:
                proxy_dict = await self.proxy_pool.get_proxy()
                if proxy_dict:
                    # 从proxy_dict中提取代理信息
                    proxy_url = proxy_dict.get("http://") or proxy_dict.get("https://")
                    if proxy_url:
                        # 解析proxy_url
                        if "@" in proxy_url:
                            # 格式: http://username:password@host:port
                            parts = proxy_url.split("://")[1].split("@")
                            auth = parts[0].split(":")
                            server = parts[1]
                            proxy_config = {
                                "server": f"http://{server}",
                                "username": auth[0],
                                "password": auth[1]
                            }
                        else:
                            # 格式: http://host:port
                            proxy_config = {"server": proxy_url}

            # 启动浏览器
            # 注意: 这里使用chromium,也可以改为firefox或webkit
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,  # 无头模式(不显示浏览器窗口)
                proxy=proxy_config       # 代理配置
            )

            # 创建浏览器上下文(相当于一个独立的浏览器会话)
            context_options = {
                "viewport": self.viewport,                 # 视口大小(影响页面渲染)
                "user_agent": self.get_random_user_agent(), # 随机User-Agent
            }

            # 添加额外的请求头
            if self.extra_headers:
                context_options["extra_http_headers"] = self.extra_headers

            self.context = await self.browser.new_context(**context_options)

            # 设置Cookie(例如登录状态)
            if self.cookies:
                await self.context.add_cookies(self.cookies)

            logger.info("Browser initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def close_browser(self):
        """关闭浏览器实例"""
        try:
            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Browser closed successfully")

        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def new_page(self) -> Page:
        """创建新页面"""
        if not self.context:
            await self.init_browser()

        page = await self.context.new_page()
        return page

    async def fetch_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        wait_timeout: Optional[int] = None,
        scroll_count: int = 0,
        scroll_delay: int = 1000,
        execute_script: Optional[str] = None,
        click_selectors: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        加载页面并返回HTML内容

        Args:
            url: 目标URL
            wait_selector: 等待的选择器
            wait_timeout: 等待超时时间(毫秒)
            scroll_count: 滚动次数(模拟下拉加载)
            scroll_delay: 滚动延迟(毫秒)
            execute_script: 要执行的JavaScript代码
            click_selectors: 要点击的元素选择器列表

        Returns:
            页面HTML内容或None
        """
        wait_timeout = wait_timeout or self.timeout
        page = None

        for attempt in range(self.max_retries):
            try:
                page = await self.new_page()
                logger.info(f"Loading page: {url} (attempt {attempt + 1}/{self.max_retries})")

                # 导航到页面
                await page.goto(url, timeout=wait_timeout, wait_until="domcontentloaded")

                # 等待特定选择器
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=wait_timeout)

                # 执行滚动操作(模拟用户行为,触发懒加载)
                # 很多网站使用"无限滚动"加载更多内容,需要滚动到底部才能触发加载
                for i in range(scroll_count):
                    await page.mouse.wheel(0, 2000)  # 向下滚动2000像素
                    await page.wait_for_timeout(scroll_delay)  # 等待页面加载
                    logger.debug(f"Scrolled {i + 1}/{scroll_count}")

                # 点击指定元素(如"展开"按钮)
                # 有些网站的内容默认是折叠的,需要点击"展开"、"查看更多"等按钮
                # 例如: 评论区、菜谱步骤、食材列表等
                if click_selectors:
                    for selector in click_selectors:
                        try:
                            elements = page.locator(selector)  # 使用XPath或CSS选择器定位元素
                            count = await elements.count()
                            logger.info(f"Found {count} elements matching '{selector}'")

                            for i in range(count):
                                try:
                                    await elements.nth(i).click(timeout=5000)  # 点击第i个元素
                                    await page.wait_for_timeout(1000)  # 等待展开动画完成
                                    logger.debug(f"Clicked element {i + 1}/{count}")
                                except Exception as e:
                                    logger.warning(f"Failed to click element {i + 1}: {e}")
                                    break  # 如果某个元素点击失败,停止点击剩余元素
                        except Exception as e:
                            logger.warning(f"Failed to process selector '{selector}': {e}")

                # 执行自定义JavaScript
                if execute_script:
                    await page.evaluate(execute_script)

                # 获取页面内容
                content = await page.content()

                # 关闭页面
                await page.close()

                # 报告代理成功
                if self.proxy_pool:
                    proxy_dict = await self.proxy_pool.get_proxy()
                    if proxy_dict:
                        await self.proxy_pool.report_success(proxy_dict)

                self.stats["pages_loaded"] += 1
                logger.info(f"Successfully loaded page: {url}")

                # 延迟
                await self.delay()

                return content

            except Exception as e:
                logger.error(f"Failed to load page (attempt {attempt + 1}/{self.max_retries}): {e}")

                if page:
                    await page.close()

                # 报告代理失败
                if self.proxy_pool:
                    proxy_dict = await self.proxy_pool.get_proxy()
                    if proxy_dict:
                        await self.proxy_pool.report_failure(proxy_dict)

                # 重试前等待
                if attempt < self.max_retries - 1:
                    retry_delay = (attempt + 1) * 2
                    logger.info(f"Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)

        self.stats["pages_failed"] += 1
        logger.error(f"Failed to load page after {self.max_retries} attempts: {url}")
        return None

    async def screenshot(
        self,
        url: str,
        output_path: str,
        full_page: bool = True
    ) -> bool:
        """
        截图页面

        Args:
            url: 目标URL
            output_path: 保存路径
            full_page: 是否截取整页

        Returns:
            是否成功
        """
        page = None
        try:
            page = await self.new_page()
            await page.goto(url, timeout=self.timeout)
            await page.screenshot(path=output_path, full_page=full_page)
            await page.close()
            logger.info(f"Screenshot saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            if page:
                await page.close()
            return False

    async def delay(self):
        """随机延迟"""
        delay_time = random.uniform(*self.request_delay)
        logger.debug(f"Sleeping for {delay_time:.2f}s")
        await asyncio.sleep(delay_time)

    @abstractmethod
    async def parse(self, html_content: str, url: str) -> List[Dict]:
        """
        解析页面内容(子类必须实现)

        Args:
            html_content: HTML内容
            url: 页面URL

        Returns:
            解析后的数据列表
        """
        pass

    @abstractmethod
    async def run(self, **kwargs) -> List[Dict]:
        """
        运行爬虫(子类必须实现)

        Returns:
            爬取的数据列表
        """
        pass

    def start_stats(self):
        """开始统计"""
        self.stats["start_time"] = datetime.now()
        logger.info(f"BrowserCrawler '{self.name}' started at {self.stats['start_time']}")

    def end_stats(self):
        """结束统计"""
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info(f"BrowserCrawler '{self.name}' finished")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Pages loaded: {self.stats['pages_loaded']}")
        logger.info(f"Pages failed: {self.stats['pages_failed']}")
        logger.info(f"Items scraped: {self.stats['items_scraped']}")

        if self.stats["pages_loaded"] > 0:
            success_rate = self.stats["pages_loaded"] / (
                self.stats["pages_loaded"] + self.stats["pages_failed"]
            )
            logger.info(f"Success rate: {success_rate:.2%}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats["start_time"] and stats["end_time"]:
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        return stats

    async def __aenter__(self):
        """支持async with语法"""
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支持async with语法"""
        await self.close_browser()


class HybridCrawler(BrowserCrawler):
    """
    混合爬虫基类
    结合requests(快速)和Playwright(动态页面)
    """

    def __init__(self, *args, use_browser_for_dynamic: bool = True, **kwargs):
        """
        初始化混合爬虫

        Args:
            use_browser_for_dynamic: 是否对动态页面使用浏览器
        """
        super().__init__(*args, **kwargs)
        self.use_browser_for_dynamic = use_browser_for_dynamic

        # 用于requests的session
        self.session = None

    def init_session(self):
        """初始化requests session"""
        import httpx

        if not self.session:
            self.session = httpx.AsyncClient(timeout=30.0)
            logger.info("HTTP session initialized")

    async def close_session(self):
        """关闭requests session"""
        if self.session:
            await self.session.aclose()
            self.session = None
            logger.info("HTTP session closed")

    async def fetch_static(self, url: str, **kwargs) -> Optional[str]:
        """
        使用requests获取静态页面(快速)

        Args:
            url: 目标URL
            **kwargs: 传递给httpx.get的参数

        Returns:
            HTML内容或None
        """
        if not self.session:
            self.init_session()

        try:
            headers = {"User-Agent": self.get_random_user_agent()}
            headers.update(self.extra_headers)

            # 获取代理
            proxies = None
            if self.proxy_pool:
                proxies = await self.proxy_pool.get_proxy()

            response = await self.session.get(
                url,
                headers=headers,
                proxies=proxies,
                **kwargs
            )
            response.raise_for_status()

            logger.info(f"Successfully fetched static page: {url}")
            return response.text

        except Exception as e:
            logger.error(f"Failed to fetch static page: {e}")
            return None

    async def close(self):
        """关闭所有资源"""
        await self.close_browser()
        await self.close_session()

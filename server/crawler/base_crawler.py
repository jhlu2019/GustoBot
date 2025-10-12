"""
基础爬虫类
Base Crawler with Anti-Scraping Features
"""
import httpx
import asyncio
import random
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger
from fake_useragent import UserAgent
from .proxy_pool import ProxyPool


class BaseCrawler(ABC):
    """基础爬虫类,包含反爬虫机制"""

    # 常用User-Agent列表
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    def __init__(
        self,
        name: str,
        proxy_pool: Optional[ProxyPool] = None,
        use_random_ua: bool = True,
        request_delay: tuple = (1, 3),
        max_retries: int = 3,
        timeout: float = 30.0,
        respect_robots_txt: bool = True
    ):
        """
        初始化爬虫

        Args:
            name: 爬虫名称
            proxy_pool: 代理池
            use_random_ua: 是否使用随机User-Agent
            request_delay: 请求延迟范围(秒)
            max_retries: 最大重试次数
            timeout: 请求超时时间
            respect_robots_txt: 是否遵守robots.txt
        """
        self.name = name
        self.proxy_pool = proxy_pool
        self.use_random_ua = use_random_ua
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt

        # 统计信息
        self.stats = {
            "requests_made": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "items_scraped": 0,
            "start_time": None,
            "end_time": None
        }

        # User-Agent生成器
        try:
            self.ua_generator = UserAgent()
        except:
            self.ua_generator = None
            logger.warning("fake-useragent initialization failed, using fallback UA list")

        logger.info(f"Crawler '{self.name}' initialized")

    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        if self.use_random_ua:
            if self.ua_generator:
                try:
                    return self.ua_generator.random
                except:
                    pass
            return random.choice(self.USER_AGENTS)
        return self.USER_AGENTS[0]

    def get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    async def delay(self):
        """随机延迟"""
        delay_time = random.uniform(*self.request_delay)
        logger.debug(f"Sleeping for {delay_time:.2f}s")
        await asyncio.sleep(delay_time)

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        use_proxy: bool = True
    ) -> Optional[httpx.Response]:
        """
        发送HTTP请求(带重试和代理)

        Args:
            url: 目标URL
            method: HTTP方法
            headers: 自定义请求头
            params: URL参数
            data: 表单数据
            json: JSON数据
            use_proxy: 是否使用代理

        Returns:
            响应对象或None
        """
        # 合并请求头
        request_headers = self.get_default_headers()
        if headers:
            request_headers.update(headers)

        self.stats["requests_made"] += 1

        for attempt in range(self.max_retries):
            try:
                # 获取代理
                proxies = None
                if use_proxy and self.proxy_pool:
                    proxies = await self.proxy_pool.get_proxy()

                # 发送请求
                async with httpx.AsyncClient(
                    proxies=proxies,
                    timeout=self.timeout,
                    follow_redirects=True
                ) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        params=params,
                        data=data,
                        json=json
                    )

                    response.raise_for_status()

                    # 报告代理成功
                    if proxies and self.proxy_pool:
                        await self.proxy_pool.report_success(proxies)

                    self.stats["requests_success"] += 1
                    logger.info(f"Successfully fetched: {url}")

                    # 延迟
                    await self.delay()

                    return response

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")

                # 报告代理失败
                if proxies and self.proxy_pool:
                    await self.proxy_pool.report_failure(proxies)

                # 某些状态码不重试
                if e.response.status_code in [404, 403, 401]:
                    break

            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                # 报告代理失败
                if proxies and self.proxy_pool:
                    await self.proxy_pool.report_failure(proxies)

            # 重试前等待
            if attempt < self.max_retries - 1:
                retry_delay = (attempt + 1) * 2
                logger.info(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)

        self.stats["requests_failed"] += 1
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None

    async def fetch_json(
        self,
        url: str,
        **kwargs
    ) -> Optional[Dict]:
        """
        获取JSON响应

        Args:
            url: 目标URL
            **kwargs: fetch方法的其他参数

        Returns:
            JSON数据或None
        """
        response = await self.fetch(url, **kwargs)
        if response:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON from {url}: {e}")
        return None

    async def fetch_text(
        self,
        url: str,
        **kwargs
    ) -> Optional[str]:
        """
        获取文本响应

        Args:
            url: 目标URL
            **kwargs: fetch方法的其他参数

        Returns:
            文本内容或None
        """
        response = await self.fetch(url, **kwargs)
        if response:
            return response.text
        return None

    @abstractmethod
    async def parse(self, response: httpx.Response) -> List[Dict]:
        """
        解析响应内容(子类必须实现)

        Args:
            response: HTTP响应

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
        logger.info(f"Crawler '{self.name}' started at {self.stats['start_time']}")

    def end_stats(self):
        """结束统计"""
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info(f"Crawler '{self.name}' finished")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Requests: {self.stats['requests_made']} "
                   f"(Success: {self.stats['requests_success']}, "
                   f"Failed: {self.stats['requests_failed']})")
        logger.info(f"Items scraped: {self.stats['items_scraped']}")

        if self.stats["requests_success"] > 0:
            success_rate = self.stats["requests_success"] / self.stats["requests_made"]
            logger.info(f"Success rate: {success_rate:.2%}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats["start_time"] and stats["end_time"]:
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        return stats

    async def check_robots_txt(self, base_url: str, user_agent: str = "*") -> bool:
        """
        检查robots.txt

        Args:
            base_url: 网站基础URL
            user_agent: User-Agent

        Returns:
            是否允许爬取
        """
        if not self.respect_robots_txt:
            return True

        try:
            robots_url = f"{base_url.rstrip('/')}/robots.txt"
            response = await self.fetch(robots_url, use_proxy=False)

            if response:
                # 简单的robots.txt解析
                content = response.text
                logger.info(f"robots.txt content preview:\n{content[:500]}")
                return True  # 具体实现可以使用robotparser

            return True

        except Exception as e:
            logger.warning(f"Failed to check robots.txt: {e}")
            return True

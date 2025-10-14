"""
代理池管理器
Proxy Pool Manager with validation and rotation
"""
import httpx
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import random


@dataclass
class Proxy:
    """代理信息"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    success_count: int = 0
    fail_count: int = 0
    last_used: Optional[datetime] = None
    last_check: Optional[datetime] = None
    response_time: float = 0.0
    is_active: bool = True

    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def to_dict(self) -> Dict:
        """转换为httpx代理配置"""
        return {
            "http://": self.url,
            "https://": self.url
        }


class ProxyPool:
    """代理池管理器"""

    def __init__(
        self,
        proxies: Optional[List[Dict]] = None,
        check_interval: int = 300,
        max_fail_count: int = 5,
        timeout: float = 10.0
    ):
        """
        初始化代理池

        Args:
            proxies: 代理列表 [{"host": "...", "port": 8080, ...}]
            check_interval: 健康检查间隔(秒)
            max_fail_count: 最大失败次数
            timeout: 代理测试超时时间
        """
        self.proxies: List[Proxy] = []
        self.check_interval = check_interval
        self.max_fail_count = max_fail_count
        self.timeout = timeout
        self._lock = asyncio.Lock()

        if proxies:
            for proxy_dict in proxies:
                self.add_proxy(**proxy_dict)

        logger.info(f"ProxyPool initialized with {len(self.proxies)} proxies")

    def add_proxy(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        protocol: str = "http"
    ):
        """添加代理"""
        proxy = Proxy(
            host=host,
            port=port,
            username=username,
            password=password,
            protocol=protocol
        )
        self.proxies.append(proxy)
        logger.debug(f"Added proxy: {host}:{port}")

    async def get_proxy(self) -> Optional[Dict]:
        """
        获取一个可用代理

        Returns:
            代理配置字典,或None
        """
        async with self._lock:
            if not self.proxies:
                return None

            # 过滤活跃代理
            active_proxies = [p for p in self.proxies if p.is_active]
            if not active_proxies:
                logger.warning("No active proxies available")
                return None

            # 按成功率和响应时间排序
            active_proxies.sort(
                key=lambda p: (p.success_rate, -p.response_time),
                reverse=True
            )

            # 使用加权随机选择(前20%代理有更高概率)
            top_20_percent = max(1, len(active_proxies) // 5)
            weights = [2 if i < top_20_percent else 1 for i in range(len(active_proxies))]

            proxy = random.choices(active_proxies, weights=weights)[0]
            proxy.last_used = datetime.now()

            logger.debug(f"Selected proxy: {proxy.host}:{proxy.port} (success rate: {proxy.success_rate:.2%})")
            return proxy.to_dict()

    async def report_success(self, proxy_dict: Dict):
        """报告代理请求成功"""
        async with self._lock:
            proxy = self._find_proxy_by_dict(proxy_dict)
            if proxy:
                proxy.success_count += 1
                logger.debug(f"Proxy {proxy.host}:{proxy.port} success count: {proxy.success_count}")

    async def report_failure(self, proxy_dict: Dict):
        """报告代理请求失败"""
        async with self._lock:
            proxy = self._find_proxy_by_dict(proxy_dict)
            if proxy:
                proxy.fail_count += 1
                logger.warning(f"Proxy {proxy.host}:{proxy.port} fail count: {proxy.fail_count}")

                # 失败次数过多则禁用
                if proxy.fail_count >= self.max_fail_count:
                    proxy.is_active = False
                    logger.error(f"Proxy {proxy.host}:{proxy.port} disabled due to too many failures")

    def _find_proxy_by_dict(self, proxy_dict: Dict) -> Optional[Proxy]:
        """通过代理字典查找代理对象"""
        if not proxy_dict:
            return None

        proxy_url = proxy_dict.get("http://") or proxy_dict.get("https://")
        if not proxy_url:
            return None

        for proxy in self.proxies:
            if proxy.url == proxy_url:
                return proxy
        return None

    async def check_proxy(self, proxy: Proxy, test_url: str = "https://httpbin.org/ip") -> bool:
        """
        检查代理是否可用

        Args:
            proxy: 代理对象
            test_url: 测试URL

        Returns:
            是否可用
        """
        try:
            start_time = datetime.now()
            async with httpx.AsyncClient(proxies=proxy.to_dict(), timeout=self.timeout) as client:
                response = await client.get(test_url)
                response.raise_for_status()

            response_time = (datetime.now() - start_time).total_seconds()
            proxy.response_time = response_time
            proxy.last_check = datetime.now()
            proxy.is_active = True

            logger.info(f"Proxy {proxy.host}:{proxy.port} is healthy (response time: {response_time:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Proxy {proxy.host}:{proxy.port} check failed: {e}")
            proxy.is_active = False
            proxy.last_check = datetime.now()
            return False

    async def health_check(self, test_url: str = "https://httpbin.org/ip"):
        """对所有代理进行健康检查"""
        logger.info(f"Starting health check for {len(self.proxies)} proxies")

        tasks = [self.check_proxy(proxy, test_url) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        active_count = sum(1 for r in results if r is True)
        logger.info(f"Health check completed: {active_count}/{len(self.proxies)} proxies active")

    async def start_health_check_loop(self, test_url: str = "https://httpbin.org/ip"):
        """启动健康检查循环"""
        logger.info("Starting proxy health check loop")
        while True:
            await self.health_check(test_url)
            await asyncio.sleep(self.check_interval)

    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        active_proxies = [p for p in self.proxies if p.is_active]
        return {
            "total_proxies": len(self.proxies),
            "active_proxies": len(active_proxies),
            "inactive_proxies": len(self.proxies) - len(active_proxies),
            "average_success_rate": sum(p.success_rate for p in self.proxies) / len(self.proxies) if self.proxies else 0,
            "average_response_time": sum(p.response_time for p in active_proxies) / len(active_proxies) if active_proxies else 0
        }

    @classmethod
    def from_file(cls, filepath: str) -> "ProxyPool":
        """
        从文件加载代理列表

        文件格式(每行一个代理):
        host:port
        host:port:username:password
        protocol://host:port
        protocol://username:password@host:port
        """
        proxies = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    proxy_dict = cls._parse_proxy_line(line)
                    if proxy_dict:
                        proxies.append(proxy_dict)

            logger.info(f"Loaded {len(proxies)} proxies from {filepath}")
            return cls(proxies=proxies)

        except Exception as e:
            logger.error(f"Failed to load proxies from file: {e}")
            return cls()

    @staticmethod
    def _parse_proxy_line(line: str) -> Optional[Dict]:
        """解析代理行"""
        try:
            # protocol://username:password@host:port
            if '://' in line:
                protocol, rest = line.split('://', 1)
                if '@' in rest:
                    auth, hostport = rest.split('@', 1)
                    username, password = auth.split(':', 1)
                    host, port = hostport.split(':', 1)
                    return {
                        "host": host,
                        "port": int(port),
                        "username": username,
                        "password": password,
                        "protocol": protocol
                    }
                else:
                    host, port = rest.split(':', 1)
                    return {
                        "host": host,
                        "port": int(port),
                        "protocol": protocol
                    }

            # host:port:username:password
            elif line.count(':') == 3:
                host, port, username, password = line.split(':', 3)
                return {
                    "host": host,
                    "port": int(port),
                    "username": username,
                    "password": password
                }

            # host:port
            elif line.count(':') == 1:
                host, port = line.split(':', 1)
                return {
                    "host": host,
                    "port": int(port)
                }

            else:
                logger.warning(f"Invalid proxy format: {line}")
                return None

        except Exception as e:
            logger.error(f"Failed to parse proxy line '{line}': {e}")
            return None

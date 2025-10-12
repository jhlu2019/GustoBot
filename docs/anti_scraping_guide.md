# 反爬虫最佳实践指南

本指南详细介绍如何规避常见的反爬虫机制,实现稳定、高效、合法的数据采集。

## 📚 目录

- [法律与道德准则](#法律与道德准则)
- [常见反爬虫机制](#常见反爬虫机制)
- [反爬虫策略](#反爬虫策略)
- [代理池最佳实践](#代理池最佳实践)
- [浏览器指纹对抗](#浏览器指纹对抗)
- [请求频率控制](#请求频率控制)
- [验证码处理](#验证码处理)
- [动态内容处理](#动态内容处理)
- [监控与应急](#监控与应急)
- [案例分析](#案例分析)

---

## 法律与道德准则

### ⚖️ 法律合规

在开始爬取之前，请确保：

1. **遵守Robots.txt** ✅
   - 所有爬虫默认遵守robots.txt协议
   - 不爬取被禁止的路径

2. **遵守网站服务条款** ✅
   - 阅读目标网站的服务条款
   - 不爬取明确禁止采集的内容

3. **尊重版权** ✅
   - 仅爬取公开数据
   - 不用于商业用途（除非获得授权）
   - 注明数据来源

4. **个人隐私保护** ✅
   - 不采集个人隐私信息
   - 遵守GDPR、个人信息保护法等法规

### 🤝 道德准则

1. **合理的爬取频率**
   - 不对目标服务器造成过大压力
   - 避开网站高峰时段

2. **标识身份**
   - 使用描述性的User-Agent
   - 提供联系方式（如有必要）

3. **尊重服务器资源**
   - 使用缓存，避免重复请求
   - 实现增量爬取

---

## 常见反爬虫机制

### 1. 基于请求头的检测

**检测方法**:
- 检查User-Agent
- 检查Referer
- 检查Accept-Language、Accept-Encoding等

**特征**:
```
爬虫: User-Agent: python-requests/2.31.0
正常: User-Agent: Mozilla/5.0 (Windows NT 10.0...) Chrome/120.0.0.0
```

### 2. 基于IP的限制

**限制方式**:
- 单IP请求频率限制
- IP黑名单
- IP地域限制

**现象**:
- 429 Too Many Requests
- 403 Forbidden
- 直接返回空数据

### 3. 基于Cookie/Session的验证

**机制**:
- 首次访问设置Cookie
- 后续请求需要带上Cookie
- Session超时机制

### 4. JavaScript挑战

**类型**:
- 计算挑战（eval、复杂运算）
- 浏览器环境检测
- Canvas指纹
- WebGL指纹

### 5. 动态加密参数

**表现**:
- 请求参数包含签名: `sign=abc123`
- 签名通过JavaScript动态生成
- 时间戳参数: `timestamp=1234567890`

### 6. 验证码

**类型**:
- 图片验证码
- 滑动验证码（极验、腾讯云等）
- 点击验证码
- reCAPTCHA

### 7. 行为分析

**监控指标**:
- 鼠标轨迹
- 键盘输入
- 页面停留时间
- 滚动速度
- 点击位置

---

## 反爬虫策略

### 策略1: User-Agent轮换

**问题**: 默认User-Agent会暴露爬虫身份

**解决方案**:

```python
from server.crawler.browser_crawler import BrowserCrawler

# 方法1: 使用内置的随机User-Agent池
crawler = BrowserCrawler(use_random_ua=True)  # 默认开启

# 方法2: 自定义User-Agent池
class CustomUACrawler(BrowserCrawler):
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0',
        # 添加更多...
    ]

# 方法3: 使用fake-useragent库（动态获取真实UA）
from fake_useragent import UserAgent
ua = UserAgent()

crawler = BrowserCrawler(
    extra_headers={"User-Agent": ua.random}
)
```

**最佳实践**:
- ✅ 使用真实浏览器的User-Agent
- ✅ 定期更新User-Agent池
- ❌ 不使用明显的爬虫UA（如python-requests）

### 策略2: IP代理池

**问题**: 单个IP频繁请求被封禁

**解决方案**:

```python
from server.crawler.proxy_pool import ProxyPool
from server.crawler.browser_crawler import BrowserCrawler

# 创建代理池
proxy_pool = ProxyPool(
    check_interval=300,    # 5分钟健康检查一次
    max_fail_count=5,      # 失败5次后禁用代理
    timeout=10.0           # 代理测试超时10秒
)

# 从文件加载代理
proxy_pool = ProxyPool.from_file("proxies.txt")

# 使用代理池
crawler = BrowserCrawler(proxy_pool=proxy_pool)
```

**代理类型选择**:

1. **数据中心代理** (Datacenter Proxies)
   - 优点: 便宜、速度快
   - 缺点: 容易被识别和封禁
   - 适用: 不严格的网站

2. **住宅代理** (Residential Proxies)
   - 优点: 真实IP，不易被封
   - 缺点: 贵、速度慢
   - 适用: 严格的网站

3. **移动代理** (Mobile Proxies)
   - 优点: 更真实，很少被封
   - 缺点: 最贵
   - 适用: 非常严格的网站

**代理获取渠道**:
- 付费代理服务: Bright Data、Oxylabs、Smartproxy
- 免费代理: 不推荐（不稳定、不安全）
- 自建代理池: 需要技术投入

### 策略3: 请求延迟

**问题**: 请求过快被识别为机器人

**解决方案**:

```python
# 方法1: 固定延迟（不推荐）
import asyncio
await asyncio.sleep(2)

# 方法2: 随机延迟（推荐）
crawler = BrowserCrawler(
    request_delay=(2, 5)  # 2-5秒随机延迟
)

# 方法3: 指数退避（重试时使用）
async def fetch_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await crawler.fetch_page(url)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s...
                await asyncio.sleep(wait_time)
            else:
                raise
```

**延迟设置建议**:

| 网站类型 | 延迟范围 | 说明 |
|---------|---------|-----|
| 宽松 | 1-2秒 | 无明显限制 |
| 一般 | 2-5秒 | 有基础限制 |
| 严格 | 5-10秒 | 严格的频率控制 |
| 极严格 | 10-30秒 | 极端反爬机制 |

### 策略4: Cookie管理

**问题**: 网站需要Cookie才能访问

**解决方案**:

```python
# 方法1: 提供初始Cookie
cookies = [
    {
        "name": "session_id",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/",
        "httpOnly": True,
        "secure": True
    }
]

crawler = BrowserCrawler(cookies=cookies)

# 方法2: 自动获取Cookie（模拟登录）
async def login_and_get_cookies():
    crawler = BrowserCrawler(headless=False)  # 显示浏览器
    await crawler.init_browser()

    page = await crawler.new_page()

    # 访问登录页
    await page.goto("https://example.com/login")

    # 填写表单
    await page.fill('input[name="username"]', "your_username")
    await page.fill('input[name="password"]', "your_password")

    # 点击登录按钮
    await page.click('button[type="submit"]')

    # 等待登录成功
    await page.wait_for_selector('div.user-profile')

    # 获取Cookie
    cookies = await crawler.context.cookies()

    # 保存Cookie
    import json
    with open("cookies.json", "w") as f:
        json.dump(cookies, f)

    await crawler.close_browser()
    return cookies

# 方法3: 从文件加载Cookie
import json
with open("cookies.json", "r") as f:
    cookies = json.load(f)

crawler = BrowserCrawler(cookies=cookies)
```

### 策略5: 模拟人类行为

**问题**: 行为特征像机器人

**解决方案**:

```python
async def human_like_crawl(crawler, url):
    """模拟人类浏览行为"""

    page = await crawler.new_page()

    # 1. 访问页面
    await page.goto(url)

    # 2. 随机等待（读取时间）
    await page.wait_for_timeout(random.randint(1000, 3000))

    # 3. 模拟鼠标移动
    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    await page.wait_for_timeout(random.randint(500, 1000))

    # 4. 模拟滚动（逐步滚动，不是一次性）
    for _ in range(3):
        scroll_amount = random.randint(300, 800)
        await page.mouse.wheel(0, scroll_amount)
        await page.wait_for_timeout(random.randint(1000, 2000))

    # 5. 模拟点击（如果需要）
    try:
        # 随机点击某个元素
        element = await page.query_selector('a')
        if element:
            await element.click()
            await page.wait_for_timeout(random.randint(500, 1500))
            await page.go_back()
    except:
        pass

    # 6. 获取内容
    content = await page.content()
    await page.close()

    return content
```

**行为模拟清单**:
- ✅ 随机停留时间
- ✅ 渐进式滚动
- ✅ 鼠标移动轨迹
- ✅ 随机点击
- ✅ 返回上一页
- ✅ 访问相关页面

### 策略6: Referer伪造

**问题**: 网站检查Referer判断请求来源

**解决方案**:

```python
# HTTP爬虫
async def fetch_with_referer(url):
    headers = {
        "Referer": "https://example.com/",  # 伪造来源
        "User-Agent": "Mozilla/5.0 ..."
    }
    response = await crawler.fetch(url, headers=headers)

# 浏览器爬虫
crawler = BrowserCrawler(
    extra_headers={
        "Referer": "https://example.com/"
    }
)
```

---

## 代理池最佳实践

### 1. 代理质量评估

```python
from server.crawler.proxy_pool import ProxyPool
import asyncio

async def evaluate_proxies():
    proxy_pool = ProxyPool.from_file("proxies.txt")

    # 健康检查
    await proxy_pool.health_check()

    # 查看统计
    stats = proxy_pool.get_stats()

    print(f"总代理数: {stats['total_proxies']}")
    print(f"活跃代理: {stats['active_proxies']}")
    print(f"平均成功率: {stats['average_success_rate']:.2%}")
    print(f"平均响应时间: {stats['average_response_time']:.2f}s")

    # 筛选优质代理
    good_proxies = [
        p for p in proxy_pool.proxies
        if p.is_active and p.success_rate > 0.8 and p.response_time < 5.0
    ]

    print(f"优质代理: {len(good_proxies)} 个")
```

### 2. 代理轮换策略

```python
# 策略1: 加权随机（内置）
# 成功率高的代理有更高概率被选中
proxy_pool = ProxyPool()  # 默认使用加权随机

# 策略2: 轮询
class RoundRobinProxyPool(ProxyPool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_index = 0

    async def get_proxy(self):
        if not self.proxies:
            return None

        active_proxies = [p for p in self.proxies if p.is_active]
        if not active_proxies:
            return None

        proxy = active_proxies[self.current_index % len(active_proxies)]
        self.current_index += 1

        return proxy.to_dict()

# 策略3: 粘性代理（同一会话使用同一代理）
class StickyProxyPool(ProxyPool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_proxies = {}

    async def get_proxy_for_session(self, session_id: str):
        if session_id in self.session_proxies:
            return self.session_proxies[session_id]

        proxy = await self.get_proxy()
        self.session_proxies[session_id] = proxy
        return proxy
```

### 3. 代理自动恢复

```python
import asyncio
from server.crawler.proxy_pool import ProxyPool

async def auto_recovery_pool():
    """自动恢复失效的代理"""
    proxy_pool = ProxyPool.from_file("proxies.txt")

    # 启动健康检查循环
    async def health_check_loop():
        while True:
            await proxy_pool.health_check()
            await asyncio.sleep(300)  # 每5分钟检查一次

    # 启动恢复循环
    async def recovery_loop():
        while True:
            # 尝试恢复失败次数多的代理
            for proxy in proxy_pool.proxies:
                if not proxy.is_active and proxy.fail_count >= proxy_pool.max_fail_count:
                    # 重置失败计数，给予重新尝试的机会
                    proxy.fail_count = 0
                    proxy.is_active = True
                    logger.info(f"尝试恢复代理: {proxy.host}:{proxy.port}")

            await asyncio.sleep(1800)  # 每30分钟尝试恢复

    # 同时运行两个循环
    await asyncio.gather(
        health_check_loop(),
        recovery_loop()
    )
```

---

## 浏览器指纹对抗

### 1. 修改浏览器指纹

```python
from playwright.async_api import async_playwright

async def stealth_browser():
    """隐身浏览器配置"""
    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',  # 禁用自动化标识
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
        ]
    )

    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
        permissions=['geolocation'],
        geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京
    )

    # 注入脚本隐藏webdriver标识
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // 隐藏Chrome标识
        window.navigator.chrome = {
            runtime: {}
        };

        // 伪造plugin数量
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // 伪造语言
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
    """)

    page = await context.new_page()
    return page
```

### 2. Canvas指纹对抗

```python
async def anti_canvas_fingerprint(page):
    """对抗Canvas指纹"""
    await page.add_init_script("""
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            // 在canvas数据上添加轻微噪声
            const context = this.getContext('2d');
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 10) - 5;
            }
            context.putImageData(imageData, 0, 0);
            return originalToDataURL.apply(this, arguments);
        };
    """)
```

---

## 请求频率控制

### 1. 令牌桶算法

```python
import asyncio
import time

class TokenBucket:
    """令牌桶限流器"""

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒生成的令牌数
            capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """获取令牌"""
        async with self._lock:
            now = time.time()
            # 添加新令牌
            self.tokens = min(
                self.capacity,
                self.tokens + (now - self.last_update) * self.rate
            )
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1):
        """等待直到获取到令牌"""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)


# 使用示例
async def rate_limited_crawl():
    # 每秒最多2个请求，桶容量10
    limiter = TokenBucket(rate=2.0, capacity=10)

    urls = [f"https://example.com/page{i}" for i in range(100)]

    for url in urls:
        await limiter.wait_for_token()  # 等待令牌
        response = await crawler.fetch_page(url)
        # 处理响应...
```

### 2. 滑动窗口算法

```python
from collections import deque
import time

class SlidingWindowLimiter:
    """滑动窗口限流器"""

    def __init__(self, max_requests: int, window_size: int):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_size: 窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()

    async def acquire(self) -> bool:
        """尝试获取请求许可"""
        now = time.time()

        # 移除窗口外的请求
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()

        # 检查是否超过限制
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    async def wait_for_slot(self):
        """等待直到有可用槽位"""
        while not await self.acquire():
            await asyncio.sleep(0.1)


# 使用示例
async def crawl_with_limit():
    # 60秒内最多100个请求
    limiter = SlidingWindowLimiter(max_requests=100, window_size=60)

    for url in urls:
        await limiter.wait_for_slot()
        response = await crawler.fetch_page(url)
```

---

## 验证码处理

### 1. 图片验证码

```python
# 方法1: 手动处理（开发阶段）
async def manual_captcha(page):
    """手动输入验证码"""
    # 等待验证码图片加载
    await page.wait_for_selector('img.captcha')

    # 截图保存验证码
    captcha_element = await page.query_selector('img.captcha')
    await captcha_element.screenshot(path='captcha.png')

    # 手动输入
    captcha_code = input("请输入验证码: ")

    # 填写验证码
    await page.fill('input[name="captcha"]', captcha_code)

# 方法2: OCR自动识别（简单验证码）
async def ocr_captcha(page):
    """使用OCR识别验证码"""
    import pytesseract
    from PIL import Image

    # 截图
    captcha_element = await page.query_selector('img.captcha')
    await captcha_element.screenshot(path='captcha.png')

    # OCR识别
    image = Image.open('captcha.png')
    captcha_code = pytesseract.image_to_string(image)

    # 填写
    await page.fill('input[name="captcha"]', captcha_code.strip())

# 方法3: 第三方打码平台
async def third_party_captcha(page, api_key):
    """使用打码平台"""
    # 1. 获取验证码图片
    captcha_url = await page.get_attribute('img.captcha', 'src')

    # 2. 提交到打码平台（示例）
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.captcha-service.com/solve',
            json={'image_url': captcha_url, 'api_key': api_key}
        )
        result = response.json()
        captcha_code = result['code']

    # 3. 填写验证码
    await page.fill('input[name="captcha"]', captcha_code)
```

### 2. 滑动验证码

```python
async def solve_slider_captcha(page):
    """解决滑动验证码"""
    # 等待滑块出现
    await page.wait_for_selector('div.slider-button')

    # 获取滑块和滑轨元素
    slider = await page.query_selector('div.slider-button')
    track = await page.query_selector('div.slider-track')

    # 获取需要滑动的距离
    track_box = await track.bounding_box()
    slider_box = await slider.bounding_box()
    distance = track_box['width'] - slider_box['width']

    # 模拟人类滑动（不是匀速）
    await slider.hover()
    await page.mouse.down()

    # 分段滑动，模拟加速减速
    steps = []
    current = 0

    # 快速阶段
    while current < distance * 0.6:
        step = random.randint(5, 15)
        steps.append(step)
        current += step

    # 减速阶段
    while current < distance * 0.95:
        step = random.randint(2, 5)
        steps.append(step)
        current += step

    # 精确调整
    steps.append(distance - current)

    # 执行滑动
    for step in steps:
        await page.mouse.move(
            slider_box['x'] + current,
            slider_box['y'],
            steps=random.randint(5, 10)
        )
        current += step
        await asyncio.sleep(random.uniform(0.01, 0.05))

    await page.mouse.up()
```

---

## 动态内容处理

### 1. AJAX数据加载

```python
async def wait_for_ajax(page, timeout=30000):
    """等待AJAX请求完成"""
    # 方法1: 等待特定元素出现
    await page.wait_for_selector('div.data-loaded', timeout=timeout)

    # 方法2: 等待网络空闲
    await page.wait_for_load_state('networkidle', timeout=timeout)

    # 方法3: 等待特定API请求
    async with page.expect_response(
        lambda response: 'api/data' in response.url
    ) as response_info:
        await page.click('button.load-more')
    response = await response_info.value
    data = await response.json()
```

### 2. 无限滚动

```python
async def scroll_to_load_all(page, max_scrolls=10):
    """滚动加载所有内容"""
    previous_height = 0

    for i in range(max_scrolls):
        # 滚动到底部
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')

        # 等待加载
        await asyncio.sleep(2)

        # 检查是否还有新内容
        current_height = await page.evaluate('document.body.scrollHeight')

        if current_height == previous_height:
            # 没有新内容，停止滚动
            break

        previous_height = current_height
        print(f"滚动第 {i+1} 次，高度: {current_height}")

    print(f"滚动完成，共滚动 {i+1} 次")
```

### 3. 懒加载图片

```python
async def load_lazy_images(page):
    """加载所有懒加载图片"""
    # 滚动触发懒加载
    await page.evaluate("""
        async () => {
            const scrollHeight = document.body.scrollHeight;
            const step = 500;

            for (let y = 0; y < scrollHeight; y += step) {
                window.scrollTo(0, y);
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }
    """)

    # 等待所有图片加载完成
    await page.wait_for_load_state('networkidle')
```

---

## 监控与应急

### 1. 监控爬虫状态

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class CrawlerMetrics:
    """爬虫指标"""
    start_time: datetime
    requests_sent: int = 0
    requests_failed: int = 0
    items_scraped: int = 0
    proxies_banned: int = 0
    captchas_encountered: int = 0

    @property
    def success_rate(self):
        total = self.requests_sent
        return (total - self.requests_failed) / total if total > 0 else 0

    @property
    def runtime_seconds(self):
        return (datetime.now() - self.start_time).total_seconds()

    def report(self):
        """生成报告"""
        return {
            "运行时长": f"{self.runtime_seconds:.0f}秒",
            "请求总数": self.requests_sent,
            "成功数": self.requests_sent - self.requests_failed,
            "失败数": self.requests_failed,
            "成功率": f"{self.success_rate:.2%}",
            "爬取条目": self.items_scraped,
            "代理被封": self.proxies_banned,
            "遇到验证码": self.captchas_encountered
        }


# 使用示例
class MonitoredCrawler(BrowserCrawler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = CrawlerMetrics(start_time=datetime.now())

    async def fetch_page(self, url, **kwargs):
        self.metrics.requests_sent += 1

        try:
            result = await super().fetch_page(url, **kwargs)
            return result
        except Exception as e:
            self.metrics.requests_failed += 1
            if "403" in str(e) or "429" in str(e):
                self.metrics.proxies_banned += 1
            raise

    def print_report(self):
        report = self.metrics.report()
        print("\n" + "="*50)
        print("爬虫运行报告")
        print("="*50)
        for key, value in report.items():
            print(f"{key}: {value}")
        print("="*50 + "\n")
```

### 2. 异常处理与重试

```python
async def smart_retry(func, max_retries=3, backoff_factor=2):
    """智能重试机制"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            error_msg = str(e)

            # 根据错误类型决定是否重试
            if "429" in error_msg:  # 频率限制
                wait_time = backoff_factor ** attempt * 10
                logger.warning(f"触发频率限制，等待 {wait_time}秒后重试...")
                await asyncio.sleep(wait_time)

            elif "403" in error_msg:  # IP被封
                logger.error("IP被封，切换代理...")
                # 标记当前代理失败
                # 自动切换到下一个代理
                await asyncio.sleep(5)

            elif "captcha" in error_msg.lower():  # 验证码
                logger.error("遇到验证码，需要人工处理")
                raise  # 不自动重试

            else:
                wait_time = backoff_factor ** attempt
                logger.warning(f"请求失败: {error_msg}，等待 {wait_time}秒后重试...")
                await asyncio.sleep(wait_time)

            if attempt == max_retries - 1:
                logger.error(f"重试 {max_retries} 次后仍然失败")
                raise

    raise Exception("重试次数耗尽")
```

### 3. 应急预案

```python
class EmergencyHandler:
    """应急处理器"""

    @staticmethod
    async def on_ip_banned(crawler):
        """IP被封时的处理"""
        logger.error("检测到IP被封，执行应急预案...")

        # 1. 停止爬虫
        await crawler.delay()

        # 2. 切换代理
        if crawler.proxy_pool:
            # 标记当前代理失败
            current_proxy = await crawler.proxy_pool.get_proxy()
            await crawler.proxy_pool.report_failure(current_proxy)

            # 健康检查，激活新代理
            await crawler.proxy_pool.health_check()

        # 3. 延长等待时间
        crawler.request_delay = (
            crawler.request_delay[0] * 2,
            crawler.request_delay[1] * 2
        )
        logger.info(f"延长延迟时间至: {crawler.request_delay}")

        # 4. 通知管理员
        # send_alert("爬虫IP被封", "需要添加新代理或调整策略")

    @staticmethod
    async def on_captcha_detected(crawler, url):
        """遇到验证码时的处理"""
        logger.warning(f"检测到验证码: {url}")

        # 1. 保存URL，稍后手动处理
        with open("captcha_urls.txt", "a") as f:
            f.write(f"{url}\n")

        # 2. 截图保存
        await crawler.screenshot(url, f"captcha_{datetime.now().timestamp()}.png")

        # 3. 通知管理员
        # send_alert("遇到验证码", f"URL: {url}")

    @staticmethod
    async def on_rate_limit(crawler):
        """触发频率限制时的处理"""
        logger.warning("触发频率限制，进入冷却期...")

        # 1. 暂停爬虫
        cooldown_time = 60 * 5  # 5分钟
        logger.info(f"暂停 {cooldown_time//60} 分钟")
        await asyncio.sleep(cooldown_time)

        # 2. 减少请求频率
        crawler.request_delay = (
            crawler.request_delay[0] * 1.5,
            crawler.request_delay[1] * 1.5
        )
```

---

## 案例分析

### 案例1: 豆瓣反爬

**反爬机制**:
- 频率限制严格
- 需要登录Cookie
- IP封禁

**应对策略**:
```python
class DoubanCrawler(BrowserCrawler):
    def __init__(self, **kwargs):
        super().__init__(
            name="DoubanCrawler",
            request_delay=(5, 10),  # 较长延迟
            **kwargs
        )

    async def run(self):
        # 1. 使用高质量住宅代理
        # 2. 携带登录Cookie
        # 3. 设置长延迟
        # 4. 限制每个IP的请求数
        pass
```

### 案例2: 淘宝反爬

**反爬机制**:
- 极强的JavaScript挑战
- 滑动验证码
- 设备指纹
- 行为分析

**应对策略**:
- 使用真实浏览器（Playwright）
- 完整模拟人类行为
- 使用住宅代理
- 避开高峰时段

---

## 总结

### ✅ 反爬虫黄金法则

1. **合法合规第一** - 遵守法律和网站规则
2. **尊重服务器** - 合理的请求频率
3. **伪装真实性** - User-Agent、Cookie、行为
4. **使用代理** - IP轮换和隐藏
5. **监控调整** - 实时监控，灵活应对

### 📊 反爬虫策略优先级

| 优先级 | 策略 | 实施难度 | 效果 |
|-------|------|---------|-----|
| 1 | 合理延迟 | ⭐ | ⭐⭐⭐⭐ |
| 2 | User-Agent轮换 | ⭐ | ⭐⭐⭐ |
| 3 | 代理池 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 4 | Cookie管理 | ⭐⭐ | ⭐⭐⭐⭐ |
| 5 | 行为模拟 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 6 | 验证码处理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

**祝你爬取成功，远离封禁！** 🛡️

更多文档: [爬虫使用指南](crawler_guide.md) | [爬虫示例](crawler_examples.md)

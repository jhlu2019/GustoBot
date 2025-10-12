# GustoBot 文档中心

欢迎来到GustoBot文档中心！这里提供了详细的使用指南、开发文档和最佳实践。

## 📚 文档目录

### 爬虫模块文档

GustoBot提供了强大的爬虫框架，支持HTTP和浏览器两种爬取模式，内置完善的反爬虫机制。

| 文档 | 描述 | 适合人群 |
|-----|------|---------|
| [爬虫使用指南](crawler_guide.md) | 爬虫模块完整使用指南，从入门到精通 | 所有用户 ⭐ |
| [爬虫实战示例](crawler_examples.md) | 8个实战案例，涵盖各种网站类型 | 进阶用户 |
| [反爬虫最佳实践](anti_scraping_guide.md) | 如何规避反爬机制，稳定采集数据 | 高级用户 |

### 快速导航

#### 🚀 我想快速开始
→ 直接看 [爬虫使用指南 - 快速开始](crawler_guide.md#快速开始)

#### 🕷️ 我想爬取特定网站
→ 参考 [爬虫实战示例](crawler_examples.md)，找到类似的例子

#### 🛡️ 我遇到了反爬问题
→ 查看 [反爬虫最佳实践](anti_scraping_guide.md)，找到解决方案

#### 📖 我想深入理解爬虫原理
→ 完整阅读 [爬虫使用指南](crawler_guide.md)

---

## 📖 爬虫文档概览

### 1. 爬虫使用指南 ([crawler_guide.md](crawler_guide.md))

**内容涵盖**:
- ✅ 概述与核心特性
- ✅ 快速开始（5分钟上手）
- ✅ 爬虫类型详解（HTTP vs 浏览器）
- ✅ 代理池配置与管理
- ✅ 命令行工具使用
- ✅ 自定义爬虫开发（完整示例）
- ✅ 数据验证与清洗
- ✅ 最佳实践
- ✅ 常见问题FAQ

**适合阅读对象**:
- 刚开始使用GustoBot爬虫的用户
- 需要了解完整功能的开发者
- 遇到问题需要查找解决方案的用户

**预计阅读时间**: 30-45分钟

---

### 2. 爬虫实战示例 ([crawler_examples.md](crawler_examples.md))

**包含8个完整示例**:

1. **下厨房网站爬虫** - 动态页面、滚动加载
2. **豆果美食爬虫** - 强反爬、代理池、搜索功能
3. **美食杰爬虫** - 静态页面、HTTP爬虫
4. **Schema.org标准网站** - 结构化数据提取
5. **两阶段爬取模式** - 列表页+详情页
6. **MongoDB集成** - 实时保存、去重
7. **批量爬取与去重** - 大规模数据采集
8. **下载图片** - 图片下载与管理

每个示例都包含：
- ✅ 完整可运行的代码
- ✅ 详细的中文注释
- ✅ 使用说明
- ✅ 注意事项

**适合阅读对象**:
- 需要参考实际代码的开发者
- 想要快速实现特定功能的用户
- 学习不同爬虫模式的开发者

**预计阅读时间**: 60-90分钟（精读）/ 15分钟（找到需要的示例）

---

### 3. 反爬虫最佳实践 ([anti_scraping_guide.md](anti_scraping_guide.md))

**核心内容**:

#### 法律与道德
- ⚖️ 法律合规（Robots.txt、版权、隐私）
- 🤝 道德准则

#### 技术对抗
- 🔍 常见反爬机制分析（7种）
- 🛡️ 反爬虫策略（6种核心策略）
  - User-Agent轮换
  - IP代理池
  - 请求延迟
  - Cookie管理
  - 模拟人类行为
  - Referer伪造

#### 高级技巧
- 🎯 代理池最佳实践（质量评估、轮换策略、自动恢复）
- 🕵️ 浏览器指纹对抗（WebDriver隐藏、Canvas指纹）
- ⏱️ 请求频率控制（令牌桶、滑动窗口）
- 🔐 验证码处理（图片验证码、滑动验证码）
- 🌐 动态内容处理（AJAX、无限滚动、懒加载）

#### 监控与应急
- 📊 监控爬虫状态
- 🚨 异常处理与重试
- 🆘 应急预案

#### 实战案例
- 📖 豆瓣反爬案例分析
- 📖 淘宝反爬案例分析

**适合阅读对象**:
- 遇到IP封禁、验证码的用户
- 需要突破反爬限制的高级用户
- 想要深入理解反爬机制的开发者

**预计阅读时间**: 90-120分钟（全面学习）/ 10分钟（查找特定问题）

---

## 🎯 使用场景导航

### 场景1: 我是新手，第一次使用爬虫

**推荐路径**:
1. 阅读 [爬虫使用指南 - 快速开始](crawler_guide.md#快速开始)
2. 运行第一个示例代码
3. 根据需要查看 [爬虫实战示例](crawler_examples.md)

### 场景2: 我需要爬取特定类型的网站

| 网站特征 | 推荐方案 |
|---------|---------|
| 静态HTML（内容在源码中） | [示例3: 美食杰爬虫](crawler_examples.md#示例3-美食杰爬虫) |
| 需要JavaScript渲染 | [示例1: 下厨房爬虫](crawler_examples.md#示例1-下厨房网站爬虫) |
| Schema.org标准 | [示例4: Schema.org网站](crawler_examples.md#示例4-schemaorg标准网站) |
| 需要搜索功能 | [示例2: 豆果美食爬虫](crawler_examples.md#示例2-豆果美食爬虫) |
| 列表页+详情页 | [示例5: 两阶段爬取](crawler_examples.md#示例5-两阶段爬取模式) |
| 需要下载图片 | [示例8: 下载图片](crawler_examples.md#示例8-下载图片) |

### 场景3: 我遇到了反爬问题

| 问题类型 | 解决方案 |
|---------|---------|
| IP被封 | [代理池配置](anti_scraping_guide.md#代理池最佳实践) |
| 访问太快被限制 | [请求频率控制](anti_scraping_guide.md#请求频率控制) |
| 需要登录Cookie | [Cookie管理](anti_scraping_guide.md#策略4-cookie管理) |
| 遇到验证码 | [验证码处理](anti_scraping_guide.md#验证码处理) |
| 检测到是爬虫 | [浏览器指纹对抗](anti_scraping_guide.md#浏览器指纹对抗) |
| 动态加载内容 | [动态内容处理](anti_scraping_guide.md#动态内容处理) |

### 场景4: 我要把数据存入数据库

**推荐方案**:
- MongoDB: [示例6: MongoDB集成](crawler_examples.md#示例6-mongodb集成)
- MySQL/PostgreSQL: 参考 [爬虫使用指南 - 自定义爬虫开发](crawler_guide.md#自定义爬虫开发)
- 直接导入知识库: 使用 `--import-kb` 参数

### 场景5: 我要批量爬取大量数据

**推荐方案**:
1. 阅读 [示例7: 批量爬取与去重](crawler_examples.md#示例7-批量爬取与去重)
2. 了解 [代理池最佳实践](anti_scraping_guide.md#代理池最佳实践)
3. 设置 [请求频率控制](anti_scraping_guide.md#请求频率控制)

---

## 💡 学习建议

### 初学者路线（1-2天）

**第1天**: 基础入门
1. ⏱️ 30分钟 - 阅读 [爬虫使用指南](crawler_guide.md) 的前3章
2. ⏱️ 30分钟 - 运行简单示例（Wikipedia爬虫）
3. ⏱️ 1小时 - 尝试修改示例代码
4. ⏱️ 1小时 - 练习使用命令行工具

**第2天**: 实战练习
1. ⏱️ 1小时 - 阅读 [爬虫实战示例](crawler_examples.md)，选择2个案例
2. ⏱️ 2小时 - 运行并理解示例代码
3. ⏱️ 1小时 - 尝试修改为自己的目标网站

### 进阶路线（3-5天）

**第3天**: 浏览器爬虫
1. ⏱️ 2小时 - 深入学习BrowserCrawler
2. ⏱️ 2小时 - 实践动态页面爬取

**第4天**: 反爬虫
1. ⏱️ 2小时 - 阅读 [反爬虫最佳实践](anti_scraping_guide.md) 前半部分
2. ⏱️ 2小时 - 配置代理池和防护措施

**第5天**: 综合项目
1. ⏱️ 4小时 - 开发一个完整的爬虫项目
2. ⏱️ 1小时 - 测试和优化

### 高级路线（持续学习）

- 📖 研究目标网站的反爬机制
- 🛠️ 优化爬虫性能和稳定性
- 📊 监控和数据分析
- 🚀 分布式爬虫架构

---

## 🔗 相关资源

### 项目文档
- [主README](../README.md) - 项目整体介绍
- [爬虫模块README](../server/crawler/README.md) - 爬虫模块概览

### 外部资源
- [Playwright文档](https://playwright.dev/python/) - 浏览器自动化
- [httpx文档](https://www.python-httpx.org/) - HTTP客户端
- [BeautifulSoup文档](https://www.crummy.com/software/BeautifulSoup/) - HTML解析
- [lxml文档](https://lxml.de/) - XML/HTML处理
- [Schema.org Recipe](https://schema.org/Recipe) - 菜谱标准

### 社区
- [GitHub Issues](https://github.com/yourusername/GustoBot/issues) - 问题反馈
- [GitHub Discussions](https://github.com/yourusername/GustoBot/discussions) - 讨论交流

---

## 📋 文档更新日志

### 2025-10 (当前版本)
- ✅ 创建爬虫使用指南
- ✅ 添加8个实战示例
- ✅ 编写反爬虫最佳实践
- ✅ 创建文档中心索引

---

## 🤝 贡献文档

发现文档错误或有改进建议？欢迎贡献！

1. Fork本仓库
2. 编辑Markdown文件
3. 提交Pull Request

---

## 📧 需要帮助？

- 💬 提交Issue: [GitHub Issues](https://github.com/yourusername/GustoBot/issues)
- 📖 查看FAQ: [爬虫使用指南 - 常见问题](crawler_guide.md#常见问题)
- 📧 联系我们: your.email@example.com

---

<div align="center">

**GustoBot 文档中心**

让数据采集变得简单、高效、合法

[⬆ 回到顶部](#gustobot-文档中心)

</div>

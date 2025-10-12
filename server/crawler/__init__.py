"""
爬虫模块
Crawler Module for Recipe Data Collection
"""
from .base_crawler import BaseCrawler
from .proxy_pool import ProxyPool
from .wikipedia_crawler import WikipediaCrawler
from .recipe_crawler import RecipeCrawler

__all__ = [
    'BaseCrawler',
    'ProxyPool',
    'WikipediaCrawler',
    'RecipeCrawler'
]

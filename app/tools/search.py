import requests
from typing import List, Dict
from app.core.config import settings

class SearchTool:
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        if not self.api_key:
            raise ValueError("未设置SERPAPI_KEY环境变量")

    def search(self, query: str, num_results: int = 3) -> List[Dict]:
        """执行搜索并返回结构化结果"""
        try:
            # 使用配置中的结果数量，如果没有则默认为2
            num_results = settings.SEARCH_RESULT_COUNT or num_results 
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "hl": "zh-CN",
                "gl": "cn"
            }

            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            return self._parse_results(response.json())
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []
    
    def _parse_results(self, data: dict) -> List[Dict]:
        results = []
        
        if "organic_results" in data:
            for item in data["organic_results"]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
                
        return results[:settings.SEARCH_RESULT_COUNT]  # 使用配置中的数量限制结果 
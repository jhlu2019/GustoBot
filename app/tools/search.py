from typing import Dict, List, Optional
import httpx
from app.config import settings
from app.core import get_logger

logger = get_logger(service="tool.search")


class SearchTool:
    """Wrapper around SerpAPI Google search results."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        default_results: Optional[int] = None,
    ) -> None:
        self.api_key = api_key or settings.SERPAPI_KEY
        if not self.api_key:
            raise RuntimeError("SERPAPI_KEY is not configured.")

        self.endpoint = (endpoint or settings.SERPAPI_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.SERPAPI_TIMEOUT
        self.default_results = default_results or settings.SEARCH_RESULT_COUNT

    def search(self, query: str, *, num_results: Optional[int] = None) -> List[Dict]:
        """执行搜索并返回结构化结果"""
        if not query:
            raise ValueError("Search query must not be empty.")

        result_count = num_results or self.default_results

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": result_count,
            "hl": "zh-CN",
            "gl": "cn",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.endpoint, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Search request failed: {}", exc)
            return []

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("Failed to decode search response: {}", exc)
            return []

        return self._parse_results(payload, limit=result_count)

    def _parse_results(self, data: Dict, *, limit: int) -> List[Dict]:
        """Normalize SerpAPI payload."""
        organic_results = data.get("organic_results") or []
        results: List[Dict] = []

        for item in organic_results:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
            if len(results) >= limit:
                break

        return results

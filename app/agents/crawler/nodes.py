"""
LangGraph nodes wrapping crawler functionality.
"""
from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, List

from app.core.logger import get_logger
from app.crawler import RecipeCrawler, WikipediaCrawler
from app.crawler.data_validator import DataValidator

from .state import (
    CrawlerInputState,
    CrawlerRunOutputState,
    CrawlerValidationOutputState,
)

logger = get_logger(service="crawler-agent")


def _instantiate_crawler(crawler_type: str, options: Dict[str, Any]):
    """
    Build a crawler instance by type.

    Browser-based crawlers are imported lazily to avoid pulling in optional
    dependencies when unused.
    """

    crawler_type = (crawler_type or "recipe").lower()

    if crawler_type == "recipe":
        return RecipeCrawler(**options)

    if crawler_type == "wikipedia":
        return WikipediaCrawler(**options)

    if crawler_type == "browser":
        try:
            from app.crawler.recipe_browser_crawler import RecipeBrowserCrawler
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Browser crawler requires Playwright support") from exc

        return RecipeBrowserCrawler(**options)

    raise ValueError(f"Unsupported crawler type '{crawler_type}'")


def create_crawler_run_node() -> Callable[[CrawlerInputState], Coroutine[Any, Any, CrawlerRunOutputState]]:
    """
    Create a node that executes one of the crawler implementations.
    """

    async def run_crawler(state: CrawlerInputState) -> CrawlerRunOutputState:
        crawler_type = (state.get("crawler_type") or "recipe").lower()
        options = state.get("crawler_options") or {}
        run_params = state.get("run_params") or {}
        prior_steps = list(state.get("steps", []))

        errors: List[str] = []
        results: List[Dict[str, Any]] = []
        stats: Dict[str, Any] = {}

        try:
            crawler = _instantiate_crawler(crawler_type, options)
        except Exception as exc:
            logger.error("Failed to instantiate crawler {}: {}", crawler_type, exc)
            errors.append(f"instantiate_error:{crawler_type}:{exc}")
            return CrawlerRunOutputState(
                type="crawler",
                raw_results=[],
                stats={},
                metadata={
                    "crawler_type": crawler_type,
                    "run_params": run_params,
                },
                errors=errors,
                steps=prior_steps + ["crawler_run"],
            )

        # Basic parameter validation per crawler type.
        missing_params: List[str] = []
        if crawler_type == "recipe":
            if not run_params.get("urls"):
                missing_params.append("urls")
        elif crawler_type == "wikipedia":
            if not (run_params.get("search_queries") or run_params.get("page_titles")):
                missing_params.append("search_queries|page_titles")
        elif crawler_type == "browser":
            if not (run_params.get("urls") or run_params.get("list_pages")):
                missing_params.append("urls|list_pages")

        if missing_params:
            message = f"missing_params:{','.join(missing_params)}"
            logger.warning("Crawler {} missing parameters: {}", crawler_type, missing_params)
            errors.append(message)
            return CrawlerRunOutputState(
                type="crawler",
                raw_results=[],
                stats=getattr(crawler, "get_stats", lambda: {})(),
                metadata={
                    "crawler_type": crawler_type,
                    "run_params": run_params,
                },
                errors=errors,
                steps=prior_steps + ["crawler_run"],
            )

        try:
            results = await crawler.run(**run_params)
            stats = getattr(crawler, "get_stats", lambda: {})()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Crawler {} execution failed: {}", crawler_type, exc)
            errors.append(f"execution_error:{crawler_type}:{exc}")
            stats = getattr(crawler, "get_stats", lambda: {})()

        metadata = {
            "crawler_type": crawler_type,
            "result_count": len(results),
            "run_params": run_params,
        }

        return CrawlerRunOutputState(
            type="crawler",
            raw_results=results,
            stats=stats,
            metadata=metadata,
            errors=errors,
            steps=prior_steps + ["crawler_run"],
        )

    return run_crawler


def create_crawler_validation_node() -> Callable[[CrawlerRunOutputState], Coroutine[Any, Any, CrawlerValidationOutputState]]:
    """
    Create a node that validates raw crawler results using the DataValidator.
    """

    async def validate_results(state: CrawlerRunOutputState) -> CrawlerValidationOutputState:
        prior_steps = list(state.get("steps", []))
        raw_results = state.get("raw_results") or []
        errors = list(state.get("errors", []))

        if not raw_results:
            metadata = {
                "input_count": 0,
                "validated_count": 0,
            }
            return CrawlerValidationOutputState(
                type="crawler_validation",
                validated_items=[],
                rejected_items=0,
                metadata=metadata,
                errors=errors,
                steps=prior_steps + ["crawler_validate"],
            )

        validated_models = DataValidator.validate_batch(raw_results)
        validated_items = [model.dict() for model in validated_models]
        rejected_items = len(raw_results) - len(validated_items)

        metadata = {
            "input_count": len(raw_results),
            "validated_count": len(validated_items),
        }

        return CrawlerValidationOutputState(
            type="crawler_validation",
            validated_items=validated_items,
            rejected_items=rejected_items,
            metadata=metadata,
            errors=errors,
            steps=prior_steps + ["crawler_validate"],
        )

    return validate_results

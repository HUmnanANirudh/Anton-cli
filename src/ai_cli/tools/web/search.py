"""Web search tool supporting Tavily API and Google Custom Search fallback."""

from typing import List, Optional
import httpx
from pydantic import BaseModel
from ai_cli.config.settings import get_settings


class SearchItem(BaseModel):
    """Single web search result item."""

    title: str
    url: str
    snippet: str
    score: Optional[float] = None


class WebSearchResult(BaseModel):
    """Aggregated web search results."""

    query: str
    provider: str
    results: List[SearchItem]
    error: Optional[str] = None


async def search_tavily(query: str, api_key: str, max_results: int = 5) -> WebSearchResult:
    """Perform web search using Tavily API."""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                return WebSearchResult(
                    query=query,
                    provider="tavily",
                    results=[],
                    error=f"Tavily API returned status {response.status_code}: {response.text}",
                )

            data = response.json()
            items: List[SearchItem] = []
            for item in data.get("results", []):
                items.append(
                    SearchItem(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        score=item.get("score"),
                    )
                )

            return WebSearchResult(query=query, provider="tavily", results=items)
        except Exception as e:
            return WebSearchResult(
                query=query,
                provider="tavily",
                results=[],
                error=f"Tavily request failed: {e}",
            )


def search_google_sync(
    query: str, api_key: str, cse_id: str, max_results: int = 5
) -> WebSearchResult:
    """Perform web search using Google Custom Search JSON API."""
    try:
        from googleapiclient.discovery import build

        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=max_results).execute()

        items: List[SearchItem] = []
        for item in res.get("items", []):
            items.append(
                SearchItem(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                )
            )

        return WebSearchResult(query=query, provider="google_custom_search", results=items)
    except Exception as e:
        return WebSearchResult(
            query=query,
            provider="google_custom_search",
            results=[],
            error=f"Google Custom Search failed: {e}",
        )


async def search_web(
    query: str,
    max_results: Optional[int] = None,
) -> WebSearchResult:
    """
    Search the web using configured provider (Tavily first, then Google Custom Search).
    """
    settings = get_settings()
    num = max_results or settings.MAX_SEARCH_RESULTS

    # 1. Try Tavily API
    if settings.TAVILY_API_KEY:
        res = await search_tavily(query, settings.TAVILY_API_KEY, num)
        if not res.error and res.results:
            return res

    # 2. Fallback to Google Custom Search
    if settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID:
        res = search_google_sync(query, settings.GOOGLE_API_KEY, settings.GOOGLE_CSE_ID, num)
        if not res.error and res.results:
            return res

    return WebSearchResult(
        query=query,
        provider="none",
        results=[],
        error="No valid search API keys configured (Set TAVILY_API_KEY or GOOGLE_API_KEY + GOOGLE_CSE_ID in .env).",
    )

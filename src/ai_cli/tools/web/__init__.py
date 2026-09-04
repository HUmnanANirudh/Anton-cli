"""Web tools package."""

from ai_cli.tools.web.retrieval import WebPageContent, clean_html, fetch_page_content
from ai_cli.tools.web.search import (
    SearchItem,
    WebSearchResult,
    search_google_sync,
    search_tavily,
    search_web,
)

__all__ = [
    "search_web",
    "search_tavily",
    "search_google_sync",
    "WebSearchResult",
    "SearchItem",
    "fetch_page_content",
    "WebPageContent",
    "clean_html",
]

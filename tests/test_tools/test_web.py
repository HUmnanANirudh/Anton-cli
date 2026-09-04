"""Unit tests for web search and retrieval tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ai_cli.tools.web.retrieval import clean_html, fetch_page_content
from ai_cli.tools.web.search import search_tavily, search_web


def test_clean_html():
    """Verify HTML cleanup and tag stripping."""
    raw_html = "<html><head><style>body { color: red; }</style></head><body><h1>Title</h1><p>Hello <b>World</b></p><script>console.log('hi');</script></body></html>"
    cleaned = clean_html(raw_html)
    assert "Title Hello World" in cleaned
    assert "color: red" not in cleaned
    assert "console.log" not in cleaned


@pytest.mark.asyncio
async def test_search_tavily_mock():
    """Verify Tavily search response parsing with mock HTTP response."""
    mock_response = {
        "results": [
            {
                "title": "LangGraph Docs",
                "url": "https://langchain-ai.github.io/langgraph/",
                "content": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
                "score": 0.98,
            }
        ]
    }

    mock_resp_obj = MagicMock()
    mock_resp_obj.status_code = 200
    mock_resp_obj.json.return_value = mock_response

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp_obj

        res = await search_tavily("LangGraph overview", api_key="test_key", max_results=1)
        assert res.provider == "tavily"
        assert len(res.results) == 1
        assert res.results[0].title == "LangGraph Docs"
        assert "LangGraph is a library" in res.results[0].snippet


@pytest.mark.asyncio
async def test_search_web_no_keys():
    """Verify graceful handling when no search keys are configured."""
    with patch("ai_cli.tools.web.search.get_settings") as mock_settings:
        mock_inst = MagicMock()
        mock_inst.TAVILY_API_KEY = None
        mock_inst.GOOGLE_API_KEY = None
        mock_inst.GOOGLE_CSE_ID = None
        mock_inst.MAX_SEARCH_RESULTS = 5
        mock_settings.return_value = mock_inst

        res = await search_web("python asyncio")
        assert res.provider == "none"
        assert "No valid search API keys configured" in (res.error or "")

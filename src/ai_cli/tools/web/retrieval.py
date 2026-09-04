"""Web content retrieval and HTML text extraction."""

import re
from typing import Optional
import httpx
from pydantic import BaseModel


class WebPageContent(BaseModel):
    """Extracted text content from a web page."""

    url: str
    title: str
    text_content: str
    status_code: int
    error: Optional[str] = None


def clean_html(html_text: str) -> str:
    """Basic HTML cleaner to extract human-readable text."""
    # Remove script and style elements
    cleaned = re.sub(r"<(script|style).*?>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def fetch_page_content(url: str, max_chars: int = 10_000) -> WebPageContent:
    """Fetch and extract text content from a web URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntonCLI/0.1.0 (Developer Tool)"
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return WebPageContent(
                    url=url,
                    title="",
                    text_content="",
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}",
                )

            # Try to find title
            title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            text = clean_html(response.text)
            if len(text) > max_chars:
                text = text[:max_chars] + "... [truncated]"

            return WebPageContent(
                url=url,
                title=title,
                text_content=text,
                status_code=response.status_code,
            )

        except Exception as e:
            return WebPageContent(
                url=url,
                title="",
                text_content="",
                status_code=0,
                error=f"Fetch failed: {e}",
            )

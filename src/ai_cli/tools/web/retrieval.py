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
    """Extract clean human-readable text and deduplicate repetitive ticker lines."""
    if not html_text:
        return ""
    # Remove script, style, svg, noscript, and iframe elements
    cleaned = re.sub(
        r"<(script|style|svg|noscript|iframe).*?>.*?</\1>",
        "",
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Remove remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Process and deduplicate repetitive lines/phrases
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in cleaned.split("\n")]
    filtered_lines = []
    prev_line = ""
    repeat_count = 0

    for line in raw_lines:
        if not line:
            continue
        if line == prev_line:
            repeat_count += 1
            if repeat_count < 2:  # allow at most 1 consecutive repeat
                filtered_lines.append(line)
        else:
            repeat_count = 0
            prev_line = line
            filtered_lines.append(line)

    text = " ".join(filtered_lines)
    # Deduplicate repeated phrases/ticker blocks
    text = re.sub(r"(\b.+?\b)(?:\s+\1){2,}", r"\1 \1", text)
    return re.sub(r"\s+", " ", text).strip()


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

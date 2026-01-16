"""Web tools for ICICL CLI."""

from typing import Any

import httpx
from bs4 import BeautifulSoup

from icicl.cli.tools.base import Tool, ToolParameter, ToolResult


class WebSearchTool(Tool):
    """Search the web using DuckDuckGo."""

    @property
    def name(self) -> str:
        return "WebSearch"

    @property
    def description(self) -> str:
        return "Search the web for current information using DuckDuckGo."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The search query",
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="Number of results to return (default: 5, max: 10)",
                required=False,
            ),
        ]

    async def execute(
        self, query: str, num_results: int = 5, **kwargs: Any
    ) -> ToolResult:
        num_results = min(num_results, 10)
        try:
            async with httpx.AsyncClient() as client:
                # Use DuckDuckGo HTML search
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; ICICL/1.0)"},
                    timeout=30,
                )

                soup = BeautifulSoup(response.text, "html.parser")
                results: list[str] = []

                for result in soup.select(".result")[:num_results]:
                    title_elem = result.select_one(".result__title")
                    snippet_elem = result.select_one(".result__snippet")
                    link_elem = result.select_one(".result__url")

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        snippet = (
                            snippet_elem.get_text(strip=True) if snippet_elem else ""
                        )
                        url = link_elem.get_text(strip=True) if link_elem else ""
                        results.append(f"**{title}**\n{url}\n{snippet}\n")

                if not results:
                    return ToolResult(output="No search results found")

                return ToolResult(output="\n".join(results))
        except Exception as e:
            return ToolResult(output=f"Search error: {e}", success=False)


class WebFetchTool(Tool):
    """Fetch and parse web page content."""

    @property
    def name(self) -> str:
        return "WebFetch"

    @property
    def description(self) -> str:
        return (
            "Fetch a web page and extract its text content. "
            "Optionally use a CSS selector to target specific elements."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="The URL to fetch",
            ),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS selector to extract specific elements (optional)",
                required=False,
            ),
        ]

    async def execute(
        self, url: str, selector: str | None = None, **kwargs: Any
    ) -> ToolResult:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; ICICL/1.0)"},
                    timeout=30,
                )

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

                if selector:
                    elements = soup.select(selector)
                    text = "\n\n".join(elem.get_text(strip=True) for elem in elements)
                else:
                    text = soup.get_text(separator="\n", strip=True)

                # Clean up whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                text = "\n".join(lines)

                # Truncate if too long
                if len(text) > 15000:
                    text = text[:15000] + "\n...(truncated)..."

                return ToolResult(output=text or "No content found")
        except Exception as e:
            return ToolResult(output=f"Fetch error: {e}", success=False)

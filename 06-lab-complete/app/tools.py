"""Read-only tools available to the production research agent."""
from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any
from urllib.parse import quote, urlparse

import requests


HTTP_TIMEOUT = 20
MAX_TOOL_TEXT = 12_000
ToolFunction = Callable[..., dict[str, Any]]


def _error(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def _domain(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def _public_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use http or https")
    hostname = (parsed.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local"):
        raise ValueError("Local and private URLs are not allowed")
    return value


def web_search(
    query: str,
    topic: str = "general",
    timeframe: str | None = None,
    max_results: int = 5,
) -> dict[str, Any]:
    """Search the web through Tavily."""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is not configured")
        max_results = max(1, min(int(max_results), 10))
        body: dict[str, Any] = {
            "query": query.strip(),
            "topic": topic if topic in {"general", "news"} else "general",
            "max_results": max_results,
            "search_depth": "basic",
        }
        if timeframe in {"day", "week", "month", "year"}:
            body["time_range"] = timeframe
        response = requests.post(
            "https://api.tavily.com/search",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        items = [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "source": _domain(item.get("url", "")),
                "summary": item.get("content"),
            }
            for item in response.json().get("results", [])
        ]
        return {"tool": "web_search", "query": query, "items": items}
    except Exception as exc:
        return _error("web_search", exc)


def read_url(url: str) -> dict[str, Any]:
    """Extract readable Markdown from a public URL through Firecrawl."""
    try:
        url = _public_http_url(url)
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY is not configured")
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        metadata = data.get("metadata") or {}
        return {
            "tool": "read_url",
            "url": url,
            "title": metadata.get("title") or url,
            "source": _domain(url),
            "content": (data.get("markdown") or "")[:MAX_TOOL_TEXT],
        }
    except Exception as exc:
        return _error("read_url", exc)


def search_papers(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
) -> dict[str, Any]:
    """Search arXiv using its public Atom API."""
    try:
        max_results = max(1, min(int(max_results), 10))
        sort_by = (
            sort_by
            if sort_by in {"relevance", "lastUpdatedDate", "submittedDate"}
            else "relevance"
        )
        terms = re.findall(r"[A-Za-z0-9_-]+", query)[:8]
        api_query = " AND ".join(f"all:{term}" for term in terms) or query
        response = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": api_query,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": "descending",
            },
            headers={
                "User-Agent": os.getenv(
                    "ARXIV_USER_AGENT",
                    "Day12-Production-Agent/1.0 (educational lab)",
                )
            },
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        for entry in root.findall("atom:entry", ns):
            get_text = lambda name: " ".join(
                (entry.findtext(f"atom:{name}", default="", namespaces=ns)).split()
            )
            items.append(
                {
                    "title": get_text("title"),
                    "summary": get_text("summary"),
                    "url": get_text("id"),
                    "published": get_text("published"),
                    "authors": [
                        author.findtext("atom:name", default="", namespaces=ns)
                        for author in entry.findall("atom:author", ns)
                    ],
                    "source": "arxiv.org",
                }
            )
        return {"tool": "search_papers", "query": query, "items": items}
    except Exception as exc:
        return _error("search_papers", exc)


def market_price(symbol: str) -> dict[str, Any]:
    """Get the latest market metadata exposed by Yahoo Finance."""
    try:
        clean_symbol = symbol.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.^=-]{1,20}", clean_symbol):
            raise ValueError("Invalid market symbol")
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(clean_symbol)}",
            headers={"User-Agent": "Day12-Production-Agent/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        meta = response.json()["chart"]["result"][0]["meta"]
        return {
            "tool": "market_price",
            "symbol": clean_symbol,
            "price": meta.get("regularMarketPrice"),
            "previous_close": meta.get("chartPreviousClose"),
            "currency": meta.get("currency"),
            "exchange": meta.get("exchangeName"),
            "market_time": meta.get("regularMarketTime"),
        }
    except Exception as exc:
        return _error("market_price", exc)


def weather(location: str) -> dict[str, Any]:
    """Get current weather from wttr.in."""
    try:
        clean_location = " ".join(location.split())
        if not clean_location or len(clean_location) > 100:
            raise ValueError("Invalid location")
        response = requests.get(
            f"https://wttr.in/{quote(clean_location)}",
            params={"format": "j1"},
            headers={"User-Agent": "Day12-Production-Agent/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        current = response.json()["current_condition"][0]
        descriptions = current.get("lang_vnm") or current.get("weatherDesc") or []
        return {
            "tool": "weather",
            "location": clean_location,
            "temperature_c": current.get("temp_C"),
            "feels_like_c": current.get("FeelsLikeC"),
            "humidity_pct": current.get("humidity"),
            "condition": descriptions[0].get("value") if descriptions else None,
            "observed_at": current.get("localObsDateTime"),
        }
    except Exception as exc:
        return _error("weather", exc)


def summarize_text(text: str, max_sentences: int = 5) -> dict[str, Any]:
    """Create a small extractive summary without another model/API call."""
    clean_text = " ".join(text.split())
    max_sentences = max(1, min(int(max_sentences), 10))
    sentences = re.split(r"(?<=[.!?])\s+", clean_text)
    summary = " ".join(sentences[:max_sentences])[:4000]
    return {
        "tool": "summarize_text",
        "summary": summary,
        "sentence_count": min(len(sentences), max_sentences),
    }


def format_digest(
    items: list[dict[str, Any]],
    headline: str = "Research digest",
) -> dict[str, Any]:
    """Format existing research items as Markdown."""
    lines = [f"## {headline}", ""]
    for item in items[:10]:
        title = str(item.get("title") or item.get("summary") or "Untitled")
        url = str(item.get("url") or "")
        summary = " ".join(str(item.get("summary") or "").split())[:300]
        label = f"[{title}]({url})" if url else title
        lines.append(f"- **{label}**: {summary}")
    return {
        "tool": "format_digest",
        "markdown": "\n".join(lines),
        "item_count": min(len(items), 10),
    }


TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "web_search": web_search,
    "read_url": read_url,
    "search_papers": search_papers,
    "market_price": market_price,
    "weather": weather,
    "summarize_text": summarize_text,
    "format_digest": format_digest,
}


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web. Use topic=news for current events. "
                "Requires TAVILY_API_KEY."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "topic": {"type": "string", "enum": ["general", "news"]},
                    "timeframe": {
                        "type": "string",
                        "enum": ["day", "week", "month", "year"],
                    },
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": (
                "Read the main content of a public HTTP(S) page. "
                "Requires FIRECRAWL_API_KEY."
            ),
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_papers",
            "description": "Search scholarly papers on arXiv.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "market_price",
            "description": "Look up the latest price for a stock or crypto symbol.",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get current weather for a city or location.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_text",
            "description": "Summarize text already supplied by the user or another tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "max_sentences": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "format_digest",
            "description": "Format collected items into a concise Markdown digest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {"type": "array", "items": {"type": "object"}},
                    "headline": {"type": "string"},
                },
                "required": ["items"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    started_at = time.monotonic()
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        result: dict[str, Any] = {
            "tool": name,
            "error": "UnknownTool",
            "message": "Tool is not registered",
        }
    else:
        try:
            result = function(**arguments)
        except Exception as exc:
            result = _error(name, exc)
    result["duration_ms"] = round((time.monotonic() - started_at) * 1000, 1)
    return result

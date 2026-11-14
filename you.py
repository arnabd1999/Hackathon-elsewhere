"""Thin async client for the You.com APIs used by Elsewhere.

Endpoints (from https://you.com/docs):
  Search   POST https://ydc-index.io/v1/search    {query, count, freshness}
  Contents POST https://ydc-index.io/v1/contents  {urls[<=10], formats, crawl_timeout}
  Research POST https://api.you.com/v1/research   {input, research_effort}
Auth: X-API-Key header, key in env YDC_API_KEY.
"""
import os
import httpx

SEARCH_URL = "https://ydc-index.io/v1/search"
CONTENTS_URL = "https://ydc-index.io/v1/contents"
RESEARCH_URL = "https://api.you.com/v1/research"


def _headers():
    key = os.getenv("YDC_API_KEY")
    if not key:
        raise RuntimeError("YDC_API_KEY is not set (see .env.example)")
    return {"X-API-Key": key, "Content-Type": "application/json"}


def _check(r: httpx.Response, name: str):
    if r.status_code >= 400:
        raise RuntimeError(f"You.com {name} failed {r.status_code}: {r.text[:300]}")


async def search(client: httpx.AsyncClient, query: str, count: int = 8, freshness: str | None = None):
    """Returns a list of web results: {url, title, description, snippets, page_age, ...}."""
    body = {"query": query, "count": count}
    if freshness:
        body["freshness"] = freshness  # day | week | month | year
    r = await client.post(SEARCH_URL, headers=_headers(), json=body, timeout=30)
    _check(r, "search")
    data = r.json()
    results = data.get("results", {}) if isinstance(data, dict) else {}
    return (results.get("web") or []) + (results.get("news") or [])


async def contents(client: httpx.AsyncClient, urls: list[str]):
    """Returns a list of {url, title, markdown}. Failed crawls have markdown=None."""
    out = []
    for i in range(0, len(urls), 10):
        batch = urls[i:i + 10]
        r = await client.post(
            CONTENTS_URL,
            headers=_headers(),
            json={"urls": batch, "formats": ["markdown"], "crawl_timeout": 15},
            timeout=90,
        )
        _check(r, "contents")
        data = r.json()
        if isinstance(data, dict):  # be tolerant of a wrapped response
            data = data.get("results") or data.get("data") or []
        out.extend(data)
    return out


async def research(client: httpx.AsyncClient, question: str, effort: str = "lite"):
    """Optional: multi-step cited answer. Used for the 'deep dive' button on one universe."""
    r = await client.post(
        RESEARCH_URL,
        headers=_headers(),
        json={"input": question, "research_effort": effort},
        timeout=180,
    )
    _check(r, "research")
    return r.json()

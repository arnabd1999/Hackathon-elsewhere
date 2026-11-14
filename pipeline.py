"""The Elsewhere agent loop. Yields events that the server streams to the browser.

  idea -> core idea + your execution (LLM)
       -> 8 divergent queries -> You.com Search (parallel)
       -> top pages -> You.com Contents
       -> extract companies + verbatim quote (LLM, parallel) -> verify quote against page (code)
       -> per company: You.com Search freshness=year -> alive/pivoted/dead + dated signal (LLM, URL checked)

Event types: stage, core, universe, status, done, error.
"""
import asyncio
import hashlib
import os
import re
from urllib.parse import urlparse

import httpx

import llm
import prompts
import you
from prompts import AXES
from verify import verify_quote

MAX_PAGES = int(os.getenv("MAX_PAGES", "18"))
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "6"))
SKIP_DOMAINS = ("youtube.com", "facebook.com", "instagram.com", "x.com", "twitter.com",
                "linkedin.com", "pinterest.com", "tiktok.com", "wikipedia.org")
# Aggregator sources: allow a couple of pages each (the companies live inside them).
AGGREGATORS = ("reddit.com", "failory.com", "producthunt.com", "ycombinator.com")


def build_queries(core: dict) -> list[dict]:
    """Every search the agent runs, tagged with the lens it came from (shown in the UI)."""
    topic = core.get("short_topic") or core.get("core_idea", "")
    qs = [{"lens": "parallel", "label": "Same idea, other execution", "q": q}
          for q in (core.get("parallel_queries") or [])[:5]]
    qs += [{"lens": "cross", "label": f"Other industry: {c.get('industry', '')}", "q": c.get("query", "")}
           for c in (core.get("cross_domain") or [])[:4] if c.get("query")]
    qs += [
        {"lens": "graveyard", "label": "Startup graveyard", "q": f"site:failory.com {topic} startup failed"},
        {"lens": "graveyard", "label": "Post-mortems", "q": f"{topic} startup shut down post-mortem why we failed"},
        {"lens": "reddit", "label": "Reddit", "q": f"site:reddit.com {topic} what tool do you use"},
        {"lens": "launches", "label": "Product Hunt", "q": f"site:producthunt.com {topic}"},
        {"lens": "launches", "label": "YC companies", "q": f"site:ycombinator.com/companies {topic}"},
    ]
    return qs


def stage(msg: str) -> dict:
    return {"type": "stage", "msg": msg}


def _domain(url: str) -> str:
    d = urlparse(url or "").netloc.lower()
    return d[4:] if d.startswith("www.") else d


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _build_universe(page: dict, c: dict, core: dict) -> dict:
    theirs = {a: str((c.get("execution") or {}).get(a, "unknown")) for a in AXES}
    div = [a for a in (c.get("divergent_axes") or []) if a in AXES]
    return {
        "id": hashlib.md5(_key(c["name"]).encode()).hexdigest()[:10],
        "name": c["name"],
        "website": c.get("website") or "",
        "one_liner": c.get("one_liner", ""),
        "source_url": page.get("url"),
        "source_title": page.get("title", ""),
        "evidence_quote": c.get("evidence_quote", ""),
        "verification": verify_quote(c.get("evidence_quote", ""), page.get("markdown") or ""),
        "execution": theirs,
        "divergent_axes": div,
        "divergence": len(div),
        "divergence_summary": c.get("divergence_summary", ""),
        "lesson": c.get("lesson", ""),
        "relationship": c.get("relationship", "collaborator"),
        "kind": "inspiration" if c.get("kind") == "inspiration" else "parallel",
        "industry": c.get("industry", ""),
        "transfer": c.get("transfer", ""),
        "lens": page.get("lens", "parallel"),
        "lens_label": page.get("lens_label", "Web"),
        "relationship_reason": c.get("relationship_reason", ""),
    }


async def _status(client, sem, u: dict) -> dict:
    base = {"type": "status", "id": u["id"]}
    try:
        res = await you.search(client, f'"{u["name"]}" funding OR launch OR shut down OR acquired',
                               count=6, freshness="year")
    except Exception as e:  # noqa: BLE001
        return {**base, "status": "unknown", "signal": f"status lookup failed: {e}"}
    if not res:
        return {**base, "status": "quiet", "signal": "No coverage found in the past year."}
    items = [{"title": r.get("title"), "url": r.get("url"), "date": r.get("page_age"),
              "description": r.get("description")} for r in res]
    async with sem:
        try:
            out = await llm.complete_json(client, prompts.STATUS, prompts.status_user(u["name"], u["one_liner"], items))
        except Exception:  # noqa: BLE001
            return {**base, "status": "unknown", "signal": ""}
    by_url = {i["url"]: i for i in items}
    src = by_url.get(out.get("signal_url"))
    return {
        **base,
        "status": out.get("status", "unknown") if src else "unknown",
        "signal": out.get("signal", "") if src else "",
        "signal_url": src["url"] if src else None,  # receipt: must be a URL we actually retrieved
        "signal_date": (src or {}).get("date"),
        "conflict": out.get("conflict", ""),
    }


async def explore(idea: str):
    sem = asyncio.Semaphore(LLM_CONCURRENCY)
    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Abstract the idea
        yield stage("Stripping your idea down to its core…")
        core = await llm.complete_json(client, prompts.DECOMPOSE, prompts.decompose_user(idea))
        ue = core.get("user_execution") or {}
        core["user_execution"] = {a: str(ue.get(a, "unspecified")) for a in AXES}
        queries = build_queries(core)
        yield {"type": "core", "core_idea": core.get("core_idea", ""),
               "core_mechanism": core.get("core_mechanism", ""),
               "user_execution": core["user_execution"], "queries": queries}

        # 2. Live web search across divergent executions
        yield stage(f"Searching the live web: {len(queries)} searches across your industry, other industries, graveyards, Reddit and launches…")
        results = await asyncio.gather(*[you.search(client, q["q"], count=8) for q in queries],
                                       return_exceptions=True)
        lists = [r if isinstance(r, list) else [] for r in results]
        if not any(lists):
            errs = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError("Search returned nothing. " + (errs[0] if errs else ""))
        per_domain, urls, lens_of = {}, [], {}
        for i in range(10):  # round-robin so every lens contributes
            for q, lst in zip(queries, lists):
                if i >= len(lst):
                    continue
                u = lst[i].get("url")
                d = _domain(u)
                if not u or not d or d.endswith(SKIP_DOMAINS) or u in lens_of:
                    continue
                cap = 2 if d.endswith(AGGREGATORS) else 1
                if per_domain.get(d, 0) >= cap:
                    continue
                per_domain[d] = per_domain.get(d, 0) + 1
                urls.append(u)
                lens_of[u] = q
        urls = urls[:MAX_PAGES]

        # 3. Read the pages
        yield stage(f"Reading {len(urls)} source pages…")
        pages = [p for p in await you.contents(client, urls) if p.get("markdown")]
        for pg in pages:
            q = lens_of.get(pg.get("url")) or {}
            pg["lens"], pg["lens_label"] = q.get("lens", "parallel"), q.get("label", "Web")

        # 4. Extract + verify, streaming universes as they're found
        yield stage("Extracting companies and checking every quote against its source…")
        queue: asyncio.Queue = asyncio.Queue()

        async def work(page):
            async with sem:
                try:
                    out = await llm.complete_json(client, prompts.EXTRACT, prompts.extract_user(core, page))
                except Exception:  # noqa: BLE001
                    out = {"companies": []}
            for c in (out.get("companies") or [])[:3]:
                if c.get("name"):
                    await queue.put((page, c))

        async def close_when_done():
            await asyncio.gather(*[work(p) for p in pages])
            await queue.put(None)

        closer = asyncio.create_task(close_when_done())
        found: dict[str, dict] = {}
        status_tasks = []
        while (item := await queue.get()) is not None:
            page, c = item
            k = _key(c["name"])
            if not k or k in found:
                continue
            u = _build_universe(page, c, core)
            found[k] = u
            yield {"type": "universe", **u}
            status_tasks.append(asyncio.create_task(_status(client, sem, u)))
        await closer

        # 5. Is each universe alive today?
        yield stage("Checking which universes are still alive today…")
        for t in asyncio.as_completed(status_tasks):
            yield await t
        yield {"type": "done", "count": len(found)}

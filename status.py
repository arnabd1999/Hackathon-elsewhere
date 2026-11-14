"""Is each company alive today? Search the past year, keep only results about THIS company, ask the LLM."""
from urllib.parse import urlparse

import llm
import prompts
import you
from verify import _squash, name_on_page


def _domain(url: str) -> str:
    d = urlparse(url or "").netloc.lower()
    return d[4:] if d.startswith("www.") else d


def relevant(results: list[dict], name: str, website: str) -> list[dict]:
    site = _domain(website) if website else ""
    keep = []
    for r in results:
        text = " ".join([r.get("title") or "", r.get("description") or "",
                         *[s for s in (r.get("snippets") or []) if isinstance(s, str)]])
        by_site = bool(site) and _domain(r.get("url")) == site
        by_url = (not site and len(_squash(name)) >= 4
                  and _squash(name) in _squash(r.get("url") or ""))
        if name_on_page(name, text) or by_site or by_url:
            keep.append(r)
    return keep


async def check_status(client, sem, u: dict) -> dict:
    base = {"type": "status", "id": u["id"]}
    try:
        res = await you.search(client, f'"{u["name"]}" funding OR launch OR shut down OR acquired',
                               count=6, freshness="year")
    except Exception as e:  # noqa: BLE001
        return {**base, "status": "unknown", "signal": f"status lookup failed: {e}"}
    res = relevant(res or [], u["name"], u.get("website", ""))
    if not res:
        return {**base, "status": "quiet", "signal": "No coverage of this company found in the past year."}
    res = sorted(res, key=lambda r: r.get("page_age") or "", reverse=True)  # undated ("") sorts last
    items = [{"title": r.get("title"), "url": r.get("url"), "date": r.get("page_age"),
              "description": r.get("description")} for r in res]
    async with sem:
        try:
            domains = list(dict.fromkeys(_domain(i["url"]) for i in items if i.get("url")))
            out = await llm.complete_json(client, prompts.STATUS, prompts.status_user(u["name"], u["one_liner"], items),
                                          domains=domains)
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

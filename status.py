"""Is each company alive today? Search the past year, keep only results about THIS company, ask the LLM."""
import re
from datetime import datetime
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


_YM = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def norm_date(v) -> str:
    """page_age -> 'YYYY-MM-DD' when it parses, else ''."""
    t = str(v or "").strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", t)
    if m:
        try:
            datetime.strptime(m.group(1), "%Y-%m-%d")
            return m.group(1)
        except ValueError:
            return ""
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(t, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def stage_fields(out: dict, by_url: dict, status_: str, signal_url) -> dict:
    """stage/funding/ticker/stage_url, only when found, valid, and backed by a retrieved URL."""
    import pipeline  # late import: pipeline imports status
    found = {}
    surl = out.get("stage_url")
    if surl and surl in by_url:
        st = pipeline.clean_stage(out.get("stage"))
        if st != "unknown":
            found["stage"] = st
        f = pipeline.clean_funding(out.get("funding"))
        if f:
            found["funding"] = f
        t = pipeline.clean_ticker(out.get("ticker"))
        if t:
            found["ticker"] = t
        if found:
            found["stage_url"] = surl
    if status_ == "shut_down":
        found["stage"] = "shut_down"
        found.setdefault("stage_url", signal_url or "")
    return found


async def check_status(client, sem, u: dict) -> dict:
    base = {"type": "status", "id": u["id"], "event_date": "", "source_date": "", "signal_date": ""}
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
    out = out if isinstance(out, dict) else {}
    by_url = {i["url"]: i for i in items}
    src = by_url.get(out.get("signal_url"))
    st = out.get("status", "unknown") if src else "unknown"
    src_date = norm_date((src or {}).get("date"))
    ev_date = str(out.get("event_date") or "").strip() if src else ""
    if not _YM.match(ev_date) or (src_date and ev_date > src_date[:7]):
        ev_date = ""  # malformed, or after the page that reports it
    return {
        **base,
        "status": st,
        "signal": out.get("signal", "") if src else "",
        "signal_url": src["url"] if src else None,  # receipt: must be a URL we actually retrieved
        "event_date": ev_date,
        "source_date": src_date,
        "signal_date": src_date,
        "conflict": out.get("conflict", ""),
        **stage_fields(out, by_url, st, src["url"] if src else None),
    }

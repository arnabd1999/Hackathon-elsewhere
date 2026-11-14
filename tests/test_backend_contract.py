"""Contract the frontend builds against: stage/funding/ticker/unknown_axes on universes, dated status
events, and the closing analysis event."""
import asyncio

import pipeline
import status
from pipeline import _build_universe, clean_funding, clean_stage, clean_ticker, market_facts

PAGE = {"url": "https://x.example/p", "markdown": "Acme sells surplus bread from bakeries at a discount in Nairobi every evening."}
MINE = {"customer": "deli owners", "geography": "New York", "business_model": "unspecified",
        "technology": "SMS", "channel": "N/A"}
CORE = {"core_idea": "x", "user_execution": MINE, "founder_industry": "Food Retail"}


def _co(**kw):
    return {"name": "Acme", "kind": "parallel", "evidence_quote": "", "one_liner": "x", **kw}


# ---- universe fields ----
def test_unknown_axes_removed_from_divergence():
    c = _co(execution={"customer": "farmers", "geography": "Kenya", "business_model": "subscription",
                       "technology": "unknown", "channel": "WhatsApp"},
            divergent_axes=["customer", "geography", "business_model", "technology", "channel"])
    u = _build_universe(PAGE, c, CORE)
    assert u["unknown_axes"] == ["business_model", "technology", "channel"]
    assert u["divergent_axes"] == ["customer", "geography"]
    assert u["divergence"] == 2


def test_unknown_variants_case_insensitive():
    c = _co(execution={"customer": "NONE", "geography": "Global", "business_model": " n/a ",
                       "technology": "Unspecified", "channel": ""})
    u = _build_universe(PAGE, c, {**CORE, "user_execution": {a: "x" for a in pipeline.AXES}})
    assert u["unknown_axes"] == pipeline.AXES


def test_stage_validation():
    assert clean_stage("Series B") == "series_b_plus"
    assert clean_stage("pre-seed") == "pre_seed"
    assert clean_stage("seed") == "seed"
    assert clean_stage("Series Z mega") == "unknown"
    assert clean_stage(None) == "unknown"


def test_ticker_validation():
    assert clean_ticker("NASDAQ:TOST") == "NASDAQ:TOST"
    assert clean_ticker("nasdaq: tost") == "NASDAQ:TOST"
    assert clean_ticker("TOST (NASDAQ)") == "NASDAQ:TOST"
    assert clean_ticker("TOST") == ""
    assert clean_ticker("unknown") == ""
    assert clean_ticker("Toast trades on the NASDAQ") == ""


def test_funding_trim():
    assert clean_funding("unknown") == ""
    assert clean_funding("  $40M   Series B, 2024 ") == "$40M Series B, 2024"
    assert len(clean_funding("x" * 200)) <= 60


def test_universe_stage_fields_and_stage_url():
    u = _build_universe(PAGE, _co(stage="Series A", funding="$5M Series A, 2023", ticker="bogus"), CORE)
    assert (u["stage"], u["funding"], u["ticker"], u["stage_url"]) == ("series_a", "$5M Series A, 2023", "", PAGE["url"])
    u = _build_universe(PAGE, _co(), CORE)
    assert (u["stage"], u["funding"], u["ticker"], u["stage_url"]) == ("unknown", "", "", "")


# ---- status fields ----
U = {"id": "abc", "name": "Acme Foods", "website": "https://www.acmefoods.com", "one_liner": "Sells food"}


def R(url, title="", age=None):
    return {"url": url, "title": title, "description": "", "snippets": [], "page_age": age}


def _status(results, llm_out, monkeypatch):
    async def search(client, q, count=8, freshness=None):
        return results

    async def cj(client, system, user, max_tokens=2000, domains=None):
        return llm_out

    monkeypatch.setattr(status.you, "search", search)
    monkeypatch.setattr(status.llm, "complete_json", cj)
    return asyncio.run(status.check_status(None, asyncio.Semaphore(1), U))


def test_status_dates_and_stage(monkeypatch):
    res = [R("https://n.example/a", "Acme Foods raises", "2026-03-04T12:00:00"),
           R("https://n.example/b", "Acme Foods funding", "2025-01-01")]
    out = _status(res, {"status": "thriving", "signal": "Raised $40M", "signal_url": "https://n.example/a",
                        "event_date": "2026-02", "stage": "Series B", "funding": "$40M Series B, 2026",
                        "ticker": "", "stage_url": "https://n.example/b"}, monkeypatch)
    assert out["event_date"] == "2026-02"
    assert out["source_date"] == out["signal_date"] == "2026-03-04"
    assert out["stage"] == "series_b_plus" and out["funding"] == "$40M Series B, 2026"
    assert out["stage_url"] == "https://n.example/b"
    assert "ticker" not in out


def test_status_event_date_not_after_source(monkeypatch):
    res = [R("https://n.example/a", "Acme Foods raises", "2026-03-04")]
    out = _status(res, {"status": "active", "signal": "x", "signal_url": "https://n.example/a",
                        "event_date": "2026-09"}, monkeypatch)
    assert out["event_date"] == ""


def test_status_drops_stage_from_unlisted_url_and_bad_dates(monkeypatch):
    res = [R("https://n.example/a", "Acme Foods raises", "3 days ago")]
    out = _status(res, {"status": "active", "signal": "x", "signal_url": "https://n.example/a",
                        "event_date": "Feb 2026", "stage": "seed", "funding": "$1M",
                        "stage_url": "https://made.up/z"}, monkeypatch)
    assert out["event_date"] == "" and out["source_date"] == "" and out["signal_date"] == ""
    for k in ("stage", "funding", "ticker", "stage_url"):
        assert k not in out


def test_status_shut_down_sets_stage(monkeypatch):
    res = [R("https://n.example/a", "Acme Foods shuts down", "2025-11-02")]
    out = _status(res, {"status": "shut_down", "signal": "Closed", "signal_url": "https://n.example/a",
                        "event_date": "2025-10"}, monkeypatch)
    assert out["stage"] == "shut_down" and out["stage_url"] == "https://n.example/a"


# ---- analysis ----
def _c(kind="parallel", status_="active", stage_="unknown", funding=""):
    return {"name": "C", "kind": kind, "status": status_, "stage": stage_, "funding": funding, "industry": "X"}


def test_market_rule():
    assert market_facts([_c()] * 5)["market"] == "crowded"
    assert market_facts([_c(stage_="seed")] * 3)["market"] == "crowded"
    assert market_facts([_c(), _c(), _c(kind="inspiration")] * 1)["market"] == "emerging"
    assert market_facts([_c(), _c(status_="shut_down"), _c(stage_="shut_down"), _c(kind="inspiration")])["market"] == "open"
    f = market_facts([_c(stage_="public"), _c(funding="$2M seed"), _c(status_="shut_down"), _c(kind="inspiration")])
    assert (f["funded"], f["dead"]) == (2, 1)


def test_analyze_falls_back_and_never_raises(monkeypatch):
    async def boom(*a, **k):
        raise RuntimeError("llm down")

    monkeypatch.setattr(pipeline.llm, "complete_json", boom)
    ev = asyncio.run(pipeline.analyze(None, {"core_idea": "x"}, [_c()] * 5))
    assert ev["type"] == "analysis" and ev["market"] == "crowded"
    assert ev["summary"].count(".") >= 2

    async def empty(*a, **k):
        return {}

    monkeypatch.setattr(pipeline.llm, "complete_json", empty)
    assert asyncio.run(pipeline.analyze(None, {}, []))["summary"]


def test_explore_emits_analysis_right_before_done(monkeypatch):
    md = "Acme Foods sells surplus bread from bakeries at a discount in Nairobi every evening."

    async def search(client, q, count=8, freshness=None):
        if freshness:  # status lookup
            return [R("https://news.example/acme", "Acme Foods raises seed", "2026-01-02")]
        return [{"url": "https://acmefoods.example/", "title": "Acme"}]

    async def contents(client, urls, crawl_timeout=8):
        return [{"url": u, "title": "Acme", "markdown": md} for u in urls]

    async def cj(client, system, user, max_tokens=2000, domains=None):
        if system == pipeline.prompts.DECOMPOSE:
            return {"core_idea": "x", "short_topic": "x", "parallel_queries": ["q"], "user_execution": MINE}
        if system == pipeline.prompts.EXTRACT:
            return {"companies": [{"name": "Acme Foods", "kind": "parallel", "evidence_quote": md,
                                   "one_liner": "bread", "stage": "unknown"}]}
        if system == pipeline.prompts.STATUS:
            return {"status": "thriving", "signal": "Seed round", "signal_url": "https://news.example/acme",
                    "event_date": "2026-01", "stage": "seed", "stage_url": "https://news.example/acme"}
        return {"summary": "One. Two."}

    monkeypatch.setattr(pipeline.you, "search", search)
    monkeypatch.setattr(pipeline.you, "contents", contents)
    monkeypatch.setattr(pipeline.llm, "complete_json", cj)

    async def run():
        return [ev async for ev in pipeline.explore("idea")]

    evs = asyncio.run(run())
    types = [e["type"] for e in evs]
    assert types[-2:] == ["analysis", "done"]
    a = evs[-2]
    assert (a["funded"], a["dead"], a["market"], a["summary"]) == (1, 0, "open", "One. Two.")
    st = next(e for e in evs if e["type"] == "status")
    assert st["stage"] == "seed" and st["event_date"] == "2026-01"

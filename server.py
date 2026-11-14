"""FastAPI server: streams the agent over Server-Sent Events and records every run for replay.

Run:  uvicorn server:app --reload --port 8000   then open http://localhost:8000
"""
import asyncio
import collections
import json
import os
import re
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import you  # noqa: E402
from pipeline import explore  # noqa: E402

# Privacy: the idea travels in the URL (/api/explore?idea=...), so request access logs would record every
# typed idea. Silence uvicorn's access log unless ACCESS_LOG=1 (render.yaml also passes --no-access-log).
if os.getenv("ACCESS_LOG", "0") != "1":
    import logging
    logging.getLogger("uvicorn.access").disabled = True

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

# Public-deploy guards (all off by default for local dev; render.yaml turns them on).
# Each live run spends You.com credits (~$0.40), so cap paid calls per rolling hour; replays stay free.
LIVE_RUNS_PER_HOUR = int(os.getenv("LIVE_RUNS_PER_HOUR", "0"))    # 0 = unlimited
DEEP_DIVES_PER_HOUR = int(os.getenv("DEEP_DIVES_PER_HOUR", "0"))  # 0 = unlimited
# On a public site, don't record visitors' ideas into the shared Replay list.
RECORD_RUNS = os.getenv("RECORD_RUNS", "1") != "0"


class HourlyCap:
    """At most `limit` calls in any rolling hour, per server process. limit <= 0 means no cap."""

    def __init__(self, limit: int, window: float = 3600.0):
        self.limit, self.window, self.calls = limit, window, collections.deque()

    def allow(self, now: float | None = None) -> bool:
        if self.limit <= 0:
            return True
        now = time.time() if now is None else now
        while self.calls and now - self.calls[0] >= self.window:
            self.calls.popleft()
        if len(self.calls) >= self.limit:
            return False
        self.calls.append(now)
        return True


explore_cap = HourlyCap(LIVE_RUNS_PER_HOUR)
deep_dive_cap = HourlyCap(DEEP_DIVES_PER_HOUR)

app = FastAPI(title="Elsewhere")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def _sse(ev: dict) -> str:
    return f"data: {json.dumps(ev)}\n\n"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50].strip("-") or "idea"


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/explore")
async def api_explore(idea: str):
    if not explore_cap.allow():
        async def capped():
            yield _sse({"type": "error", "msg": "The live demo has hit its hourly limit of live runs. "
                                               "Pick a recorded run from Replay, or try again later."})
        return StreamingResponse(capped(), media_type="text/event-stream", headers=SSE_HEADERS)

    async def gen():
        events = []
        try:
            async for ev in explore(idea):
                if ev.get("type") == "done":
                    # Sent before done: the browser closes the stream on done.
                    priv = {"type": "privacy", "stored": RECORD_RUNS,
                            "discarded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                    events.append({"t": time.time(), "ev": priv})
                    yield _sse(priv)
                events.append({"t": time.time(), "ev": ev})
                yield _sse(ev)
        except Exception as e:  # noqa: BLE001
            ev = {"type": "error", "msg": str(e)}
            events.append({"t": time.time(), "ev": ev})
            yield _sse(ev)
        finally:
            if RECORD_RUNS and any(e["ev"]["type"] == "universe" for e in events):
                (CACHE / f"{_slug(idea)}.json").write_text(json.dumps({"idea": idea, "events": events}))
            events.clear()  # nothing about this run stays in server memory

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.get("/api/demos")
def demos():
    out = []
    for p in sorted(CACHE.glob("*.json")):
        try:
            out.append({"file": p.stem, "idea": json.loads(p.read_text())["idea"]})
        except Exception:  # noqa: BLE001
            continue
    return out


SHOWCASE_MAX = 8
_showcase_cache: dict = {"key": None, "items": []}


def _build_showcase(paths) -> list[dict]:
    """Verified universes from all recordings: deduped by name, round-robin across industries."""
    candidates = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            idea = str(data.get("idea") or "")
            evs = [e.get("ev") or {} for e in data.get("events") or [] if isinstance(e, dict)]
        except Exception:  # noqa: BLE001
            continue
        statuses = {ev.get("id"): ev.get("status") for ev in evs
                    if isinstance(ev, dict) and ev.get("type") == "status" and ev.get("id") is not None}
        for ev in evs:
            if not isinstance(ev, dict) or ev.get("type") != "universe" or ev.get("verification") != "verified":
                continue
            name = str(ev.get("name") or "").strip()
            if not name:
                continue
            candidates.append({
                "name": name,
                "industry": str(ev.get("industry") or ""),
                "one_liner": str(ev.get("one_liner") or ""),
                "evidence_quote": str(ev.get("evidence_quote") or ""),
                "source_url": str(ev.get("source_url") or ""),
                "receipt_url": str(ev.get("receipt_url") or ""),
                "status": str(statuses.get(ev.get("id")) or "unknown"),
                "idea": idea,
            })
    # Best-evidenced first (stable sort keeps file/event order within a tier), then dedupe by name.
    candidates.sort(key=lambda c: -(bool(c["evidence_quote"].strip()) + bool(c["receipt_url"].strip())))
    seen, groups = set(), {}
    for c in candidates:
        k = c["name"].lower()
        if k in seen:
            continue
        seen.add(k)
        groups.setdefault(c["industry"].strip().lower(), []).append(c)
    out, queues = [], list(groups.values())
    while queues and len(out) < SHOWCASE_MAX:
        for q in queues:
            if q and len(out) < SHOWCASE_MAX:
                out.append(q.pop(0))
        queues = [q for q in queues if q]
    return out


@app.get("/api/showcase")
def showcase():
    """Free: verified companies pulled from recorded runs (no external calls). Never raises."""
    try:
        paths = sorted(CACHE.glob("*.json"))
        key = (str(CACHE), tuple((p.name, p.stat().st_mtime) for p in paths))
        if _showcase_cache["key"] != key:
            _showcase_cache["items"] = _build_showcase(paths)
            _showcase_cache["key"] = key
        return [dict(i) for i in _showcase_cache["items"]]
    except Exception:  # noqa: BLE001
        return []


@app.get("/api/replay")
async def replay(file: str, speed: float = 1.0):
    """Replays a recorded live run with its real timing (capped), for a safe stage demo."""
    p = CACHE / f"{_slug(file)}.json"
    if not p.exists():
        raise HTTPException(404, "no such recording")
    data = json.loads(p.read_text())

    async def gen():
        prev = None
        for item in data["events"]:
            if prev is not None:
                await asyncio.sleep(min(1.2, max(0.05, item["t"] - prev)) / max(speed, 0.1))
            prev = item["t"]
            yield _sse(item["ev"])

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


class DeepDiveReq(BaseModel):
    name: str
    one_liner: str = ""
    website: str = ""
    status: str = ""
    signal: str = ""
    industry: str = ""

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


@app.post("/api/deep-dive")
async def deep_dive(req: DeepDiveReq):
    """Cited You.com Research answer on why one company succeeded or failed."""
    if not deep_dive_cap.allow():
        raise HTTPException(429, "Deep dives have hit their hourly limit on this demo; try again later.")
    facts = [f"{k}: {v}" for k, v in (("one-liner", req.one_liner), ("website", req.website),
                                      ("industry", req.industry), ("last known status", req.status),
                                      ("last known signal", req.signal)) if v]
    question = (
        f"Why did or does the company {req.name} succeed or fail? What happened to it most recently? "
        "What should a founder building the same core idea somewhere else learn from it? "
        f"Known facts - {'; '.join(facts) or 'none'}."
    )
    try:
        async with httpx.AsyncClient() as client:
            data = await you.research(client, question, effort="lite")
        out = data.get("output") or {}
        sources = [{"title": s.get("title") or s["url"], "url": s["url"]}
                   for s in (out.get("sources") or []) if isinstance(s, dict) and s.get("url")][:8]
        return {"summary": out.get("content") or "", "sources": sources}
    except Exception:  # noqa: BLE001
        raise HTTPException(502, "Research service failed; try again.") from None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)

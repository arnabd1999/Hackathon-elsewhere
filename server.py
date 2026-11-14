"""FastAPI server: streams the agent over Server-Sent Events and records every run for replay.

Run:  uvicorn server:app --reload --port 8000   then open http://localhost:8000
"""
import asyncio
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

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

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
    async def gen():
        events = []
        try:
            async for ev in explore(idea):
                events.append({"t": time.time(), "ev": ev})
                yield _sse(ev)
        except Exception as e:  # noqa: BLE001
            ev = {"type": "error", "msg": str(e)}
            events.append({"t": time.time(), "ev": ev})
            yield _sse(ev)
        finally:
            if any(e["ev"]["type"] == "universe" for e in events):
                (CACHE / f"{_slug(idea)}.json").write_text(json.dumps({"idea": idea, "events": events}))

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

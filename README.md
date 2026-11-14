# Elsewhere 🪐

**Every pitch is "X for Y." Elsewhere finds every X on the live web, in your industry and far outside it, tells you which are alive today, and shows a receipt for every claim.**

Built in one day at **Ground Truth: The Live Agents Hackathon** (You.com × The Builder Series × localhost:nyc). Track: **The Analyst**.

---

## The problem

Your idea isn't new. Somewhere (another country, another customer, another industry) someone has already tried it. Some of those versions are thriving. Some quietly died last month. Together they're the best evidence a founder or investor can get, because each one is a natural experiment on a single decision.

Today, finding them is slow and unreliable:

- **VCs** ask the same first diligence question of every pitch: *who else tried this, and what happened to them?* An associate spends days answering it.
- **Founders** search only their own industry, so they miss the playbooks, partners and failures that would have saved them months.
- **Databases** match by category. They miss the same idea in a different industry, and they're slow to show who pivoted or shut down.
- **LLMs** are frozen at their training date. They can't know who raised, pivoted or died this quarter, so they make companies up.

## What Elsewhere does

Describe an idea in one line. In about 4 minutes, Elsewhere:

1. **Abstracts** it to its *core concept* and records how you execute it on 5 axes: customer, geography, business model, technology, channel.
2. **Diverges** by searching the live web through 5 lenses: the same idea executed differently, **other industries** using the same core concept, startup graveyards and post-mortems, Reddit (the tools people actually use), and launch sites (Product Hunt, YC).
3. **Reads** the best pages live and extracts each company, how it differs from you, and a verbatim quote.
4. **Verifies** each quote in code by string-matching it against the page it came from: *verified*, *partial* or *unverified*. Unverified claims stay visible but faded, never hidden and never trusted.
5. **Checks who's alive today**: past-year news per company, then a status of *thriving*, *active*, *pivoted* or *shut down*. The signal must link to a page we actually retrieved, and conflicting sources are flagged.
6. **Deep dive**: "Why did this one die?" returns a cited You.com Research answer.

### The map
- **Your idea is the sun.** Inner rings are your industry, ordered by how many execution choices differ from yours.
- **Elsewhere tab:** other industries running the same core concept.
- **World tab:** a globe of where the idea already works.
- **Graveyard tab:** the versions that died, and the lessons.
- Colors: possible **collaborator** (non-overlapping market), direct **competitor**, **shut down**. A pulsing ring means momentum this year.

## How we use the You.com API (the engine, not an add-on)

| Step | You.com endpoint | What it powers |
|---|---|---|
| Diverge | **Search** `POST ydc-index.io/v1/search` | ~14 parallel searches across 5 lenses, using `site:` operators for graveyards, Reddit, Product Hunt and YC |
| Read | **Contents** `POST ydc-index.io/v1/contents` | Live crawl of the top pages (markdown), which is the ground truth every quote is checked against |
| Alive today? | **Search** with `freshness=year` | Fresh news per company → thriving / active / pivoted / shut down, with a dated source |
| Deep dive | **Research** `POST api.you.com/v1/research` | Cited answer to "why did this version succeed or fail?" |
| Reasoning (optional) | **Research** as the model (`LLM_PROVIDER=you`) | Extraction and classification run on You.com Research, restricted to the domains we already read, so the whole agent can run on one You.com key |

Take You.com out and there's no product: every company, status and quote on the map comes from a page the agent retrieved live.

## Why it only works on the live web
"Is this company alive today?" can't be answered from training data. And the main way LLMs fail at this task is inventing companies, which is exactly what our receipt check catches on screen.

## Business
- **Founders and accelerators (wedge):** first map free, then $29/mo. Validate before you build, and find partners in non-overlapping markets.
- **VC teams (revenue):** $299/seat/mo for **watchlists** that alert you when any version of a portfolio company or pipeline deal raises, pivots or shuts down. Recurring, live, and impossible without a live-web agent.
- **Why not Crunchbase's "similar companies"?** They match by category. We match by *core idea*, show *which decision differs*, show *how each version is doing right now*, and cite every claim.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add YDC_API_KEY (+ an LLM key, or set LLM_PROVIDER=you)
uvicorn server:app --reload --port 8000
# open http://localhost:8000
```

Every live run is saved to `cache/`, and the **Replay** menu plays it back with real timing.

Tests: `python -m pytest -q`

## Code map
| File | Role |
|---|---|
| `pipeline.py` | Agent loop: abstract → diverge → read → extract → verify → status, streamed to the UI as events |
| `you.py` | You.com Search, Contents and Research client |
| `llm.py` | Provider-agnostic JSON completion (OpenAI, Anthropic or You.com Research) |
| `prompts.py` | Abstraction, extraction and status prompts |
| `verify.py` | Quote-vs-page matcher (the receipts) |
| `status.py` | Alive-today classification and conflicting-source handling |
| `server.py` | FastAPI: `/api/explore` (SSE), `/api/replay`, `/api/demos`, `/api/deep-dive` |
| `static/` | The solar-system map, globe and graveyard UI |

## How we built it
Four people and four coding agents built this in one day, coordinated through **OpenCrawl**. Each agent posted to a shared board when it took or finished a file, and searched the board before changing a shared contract such as the pipeline's event schema.

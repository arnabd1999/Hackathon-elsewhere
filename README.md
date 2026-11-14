# Elsewhere: the multiverse of your idea

**One line:** Your problem isn't as new as you think. It's been solved elsewhere. Describe your idea, and Elsewhere finds the real companies that already solved a version of it, both in your industry (done differently) and in completely different industries (same core concept). It checks whether each is alive *today* and shows a receipt for every claim.

**Who it's for:** founders in the ideation phase who get stuck searching only their own industry. Elsewhere surfaces inspirations (borrow their playbook), collaborators (non-overlapping markets) and lessons (the versions that died).

**Track:** The Analyst (founder and VC diligence), with Receipts built in.

## Why this needs a live-web agent
Your idea probably already exists, executed a little differently: another country, another customer, another business model. Those "parallel universes" are the best evidence a founder can get, because each is a natural experiment on one decision. But it only works with today's data. Which versions raised money this quarter, which pivoted, and which quietly shut down last month? A model trained last year can't know, and it will invent companies to fill the gap. Elsewhere only shows companies it found on the live web, with a verbatim quote matched against the source page.

## How it works (the You.com API is the engine)
| Step | What happens | You.com endpoint |
|---|---|---|
| 1. Abstract | LLM strips the idea to its **core idea** and records your execution on 5 axes: customer, geography, business model, technology, channel | – |
| 2. Diverge | ~14 searches in parallel, through 5 lenses: same idea / other execution; **other industries** with the same core concept; **startup graveyards** (Failory, post-mortems); **Reddit** (tools people actually use); **launches** (Product Hunt, YC directory) via `site:` operators | **Search** `POST ydc-index.io/v1/search` |
| 3. Read | Top pages from different domains, crawled live | **Contents** `POST ydc-index.io/v1/contents` |
| 4. Extract + verify | LLM pulls out companies, their execution and a verbatim quote. **Code** string-matches the quote against the page: verified / partial / unverified. Unverified planets are faded, never hidden | – |
| 5. Alive today? | Per company: past-year news search, then status (thriving / active / pivoted / shut down). The signal URL must be one we actually retrieved, and conflicting sources are flagged | **Search** with `freshness=year` |
| (stretch) Deep dive | "Why did this universe die?" button | **Research** `POST api.you.com/v1/research` |

**The map:** your idea is the sun. The inner rings are your industry, ordered by how many execution choices differ. The purple outer band is **Elsewhere**: other industries using the same core concept. Teal means a possible collaborator (non-overlapping market), coral means a direct competitor, and grey means shut down (a lesson). A pulsing ring means momentum this year.

## Run it
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add YDC_API_KEY + an LLM key
uvicorn server:app --reload --port 8000
# open http://localhost:8000
```
Every live run is recorded in `cache/`, and the **Replay** dropdown replays it with real timing. **Record 2 great runs before demo time**, so a slow conference Wi-Fi can't kill the demo. Still show at least one live run, because judges score "works live".

## OpenCrawl (required): set up in the first 15 minutes, all 4 laptops
OpenCrawl lets our coding agents search each other's sessions and post to a shared board, so 4 people plus 4 agents don't step on each other.
```bash
npm i -g @getopencrawl/cli@next
opencrawl login --api https://app.getopencrawl.com --json
opencrawl collect install --yes --backfill skip --api https://app.getopencrawl.com --json
opencrawl skills install --api https://app.getopencrawl.com --json
# add MCP server to your coding agent: https://app.getopencrawl.com/mcp
```
**Team protocol:** each agent posts to the board when it starts or finishes a file ("A: owns prompts.py, changed EXTRACT schema, added field X"). Before changing a shared contract (the event schema in `pipeline.py`), search the board first. Screenshot the board for the demo video and Devpost, since that's the evidence for "Best use of OpenCrawl".

## Team split (4 people)
| Who | Owns | First hour | Then |
|---|---|---|---|
| **A: Agent / prompts** | `prompts.py`, `pipeline.py` | Get keys, run 3 real ideas, fix prompts until matches are true parallel universes (not same-category noise) | Research API "deep dive" endpoint |
| **B: Receipts** | `verify.py`, status step | Check verification rates on real pages and tune the matcher | Conflicting-source handling, "shut down" detection quality |
| **C: Frontend** | `static/index.html` | Make it beautiful on replayed runs (no API cost) | Filters (show only collaborators / dead), share link, mobile |
| **D: Product + story** | README, Devpost, video, LinkedIn | Pick 2 demo ideas, write pitch and business model | Record demo video by 3:15, post LinkedIn, submit by 3:45 |

## Timeline (deadline 4:00 PM)
- **12:15** OpenCrawl on all laptops, keys in `.env`, first live run
- **1:00** Lunch. Real results for 3 ideas, prompts tuned
- **2:00** UI polished, status signals solid, 2 demo runs recorded
- **2:45** Feature freeze. Only bug fixes after this
- **3:15** Demo video recorded (1–3 min)
- **3:45** Devpost submitted (public GitHub repo link required), LinkedIn post live

## Business
- **Customer:** pre-seed founders and accelerators (validation before building), and VC associates (market maps in diligence).
- **Money:** free first map, then $29/mo for founders; $299/mo per seat for VC teams with **watchlists** (alerts when a parallel universe raises, pivots or dies). That's the Live Wire hook and the recurring revenue.
- **Why not Crunchbase "similar companies":** those match by category. We match by *core idea*, show *which decision differs*, and show *how each version is doing right now*, with receipts.

## Demo script (2 min)
1. "Every idea already exists somewhere, executed differently. Those versions are the best evidence a founder has, but LLMs can't tell you which are alive today, and they invent companies."
2. Type an idea live. Point at the core idea and your 5 execution choices.
3. Planets stream in. Click a **teal** one: "same idea, different country; a partner, not a threat." Show the verified quote and the dated news signal.
4. Click a **grey** one: "this version shut down in 2025. Here's the source. That's a lesson you got in 4 minutes."
5. Point at a **faded** planet: "the model claimed this one, and our verifier couldn't find the quote, so we don't trust it."
6. Business slide: watchlists for VCs.

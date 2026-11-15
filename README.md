# Elsewhere: the multiverse of your idea


**One line:** Your problem isn't as new as you think. It's been solved elsewhere. Describe your idea, and Elsewhere finds the real companies that already solved a version of it, both in your industry (done differently) and in completely different industries (same core concept). It checks whether each is alive *today* and shows a receipt for every claim.

**Who it's for:** founders in the ideation phase who get stuck searching only their own industry. Elsewhere surfaces inspirations (borrow their playbook), collaborators (non-overlapping markets) and lessons (the versions that died).

**Track:** The Analyst (founder and VC diligence), with Receipts built in.

**Live demo:** https://elsewhere-8t65.onrender.com (free hosting: the first load after 15 idle minutes takes ~30 s to wake up). Pick a run from **Replay** for an instant, free walkthrough, or type your own idea for a live run (capped at 20 live runs per hour).

**Demo video (40 s):**

https://github.com/user-attachments/assets/e9916f03-35e9-4744-b863-5d03d0f2306d

Also on YouTube: https://youtu.be/t6nW4qDTuVg

**Receipts, honestly counted:** across our two recorded demo runs, 82% of company quotes (28 of 34) are found verbatim on the source page. When the model's quote isn't on the page, we show the page's own sentence about the company and label it **partial**, never verified.

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
| 6. Deep dive | "Why did this universe die?" button on shut-down companies | **Research** `POST api.you.com/v1/research` |

**The map:** your idea is the sun. The inner rings are your industry, ordered by how many execution choices differ. The purple outer band is **Elsewhere**: other industries using the same core concept. Teal means a possible collaborator (non-overlapping market), coral means a direct competitor, and grey means shut down (a lesson). A pulsing ring means momentum this year.

## Run it
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set YDC_API_KEY and LLM_PROVIDER=you (no other key needed)
uvicorn server:app --reload --port 8000
# open http://localhost:8000   (add ?mock=1 for the offline mock data)
```
`LLM_PROVIDER=you` uses the You.com Research API as the model, so a single You.com key runs everything. An OpenAI-compatible or Anthropic key also works (see `.env.example`). Tests: `python -m pytest -q` (or `python -m unittest discover -s tests`).

**Deploy:** `render.yaml` is a Render Blueprint (one Python web service). Enter `YDC_API_KEY` in Render's dashboard, never in the repo. Public-deploy guards: `LIVE_RUNS_PER_HOUR`, `DEEP_DIVES_PER_HOUR`, and `RECORD_RUNS=0` so visitors' ideas aren't added to the public Replay list.
Every live run is recorded in `cache/`, and the **Replay** dropdown replays it with real timing. **Record 2 great runs before demo time**, so a slow conference Wi-Fi can't kill the demo. Still show at least one live run, because judges score "works live".

## Built with OpenCrawl
Four people and their coding agents (Claude Code on Claude Max and Pro, plus Codex) built this in one day. OpenCrawl was the shared memory between them.
- **Shared board:** each agent posted handoffs, ownership ("index.html is yours until 3:15"), contract changes (new event fields), merges and deploy status, so parallel agents didn't overwrite each other.
- **Agents checking each other:** one agent's review caught that auto-repaired quotes were being counted as "verified". Another agent fixed it and relabelled the demo recordings, which is why the receipt rate above is honest.
- **Session search:** agents looked up each other's past sessions (deploy steps, API findings) instead of asking a human.

## Privacy
Your idea is processed in memory for the length of the run (about 30-45 s) and is not stored by our server: no disk writes (`RECORD_RUNS=0`), no request logs (`--no-access-log`). At the end of a run the page shows a "nothing stored" receipt, and **Forget this run** clears it from your browser. To search the live web, the idea is sent to You.com under their data policy (zero data retention is available on enterprise plans). We don't claim end-to-end deletion.

## Limits, honestly
- **Specific ideas work best.** "Agentic fashion commerce" returns big generalists. "An AI stylist on WhatsApp reselling pre-owned designer clothes for students in Mumbai" returns real parallel universes.
- **Not a patent or legal novelty search.** Elsewhere finds commercial prior art (companies), not patents. Check patents before you build.
- **"Alive today" needs a dated source.** It is found for about half of companies; the rest show as quiet or unknown rather than guessed.

## What's next
Ask 2 follow-up questions when an idea is too vague; rank public companies and unicorns lower; a patent lens (Google Patents through the same You.com Search); watchlists that alert when a parallel universe raises, pivots or dies.

## Business
- **Customer:** pre-seed founders and accelerators (validation before building), and VC associates (market maps in diligence).
- **Money:** free first map, then $29/mo for founders; $299/mo per seat for VC teams with **watchlists** (alerts when a parallel universe raises, pivots or dies). That's the Live Wire hook and the recurring revenue.
- **Why not Crunchbase "similar companies":** those match by category. We match by *core idea*, show *which decision differs*, and show *how each version is doing right now*, with receipts.

## Team
Built at Ground Truth: The Live Agents Hackathon (You.com, NYC, 14 Nov 2026) by [@arnabdas1999](https://github.com/arnabdas1999), [@ssachis](https://github.com/ssachis), [@khyatithapliyal](https://github.com/khyatithapliyal) and [@Namantyagi2727](https://github.com/Namantyagi2727).

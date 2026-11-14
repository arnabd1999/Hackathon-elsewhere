# Role 2: The map (Claude Pro)

Paste this into your coding agent.

---

You're building the visual centerpiece of **Elsewhere**, a hackathon app that shows where a founder's idea already lives in other industries. Read `docs/superpowers/specs/2026-11-14-elsewhere-design.md` ("Screens" and "Event contract"). Types are in `lib/types.ts` (don't change it without telling the team). Read the event stream with `readEvents()` from `lib/ndjson.ts`.

**You own:** `components/IdeaMap.tsx`, `components/EvidencePanel.tsx`, `app/results/page.tsx` (with any route-local components under `app/results/`). Role 3 owns the cards and the home page; render their `<Cards events=... />` component under your map once it exists (agree the props with them; until then leave a placeholder).

**Build against fake data now:** `POST /api/explore` with `{idea}` streams `public/demo/fixture.json` with realistic timing (`?fast=1` skips delays). Role 1 swaps in the real pipeline later; the stream format stays the same.

**What it must do:**
1. `app/results/page.tsx`: reads `?idea=` from the URL, POSTs to `/api/explore`, accumulates events into state.
2. `IdeaMap` (`react-force-graph-2d`, already installed; it needs `dynamic(() => import(...), { ssr: false })`): the idea as a large center node labeled with the `concept`; each `industry` event adds a node that animates in, linked to the center; nodes "light up" (glow or size up) when `evidence` for them arrives. Show the industry name on each node.
3. Clicking an industry node opens `EvidencePanel`: its `why` line plus its sources as links (title + domain).
4. Loading state from the first second: e.g. a pulsing center node with "Reading the web…" so the screen is never blank.

**Make it beautiful:** dark background, one accent color, smooth motion. This is the moment judges remember.

**Done when (~1:45):** the fixture plays from an empty map to five glowing industry nodes, and clicking a node shows its sources. Then polish until 3:15. Merge to `main` when it works, and post on the OpenCrawl board.

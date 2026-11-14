# Role 3: Home page, cards, demo replay (Claude Pro)

Paste this into your coding agent.

---

You're building the entry screen and the evidence cards of **Elsewhere**, a hackathon app that shows where a founder's idea already lives in other industries. Read `docs/superpowers/specs/2026-11-14-elsewhere-design.md` ("What the user gets", "Screens", "Event contract", "Demo mode"). Types are in `lib/types.ts` (don't change it without telling the team).

**You own:** `app/page.tsx`, `components/Cards.tsx`, `components/Card.tsx`, `components/SourceChip.tsx`, `lib/replay.ts`. Role 2 owns `app/results/page.tsx` and the map; they render your `<Cards />` under the map. Agree the props with them early (suggested: `<Cards events={ExploreEvent[]} />`).

**What it must do:**
1. **Home (`app/page.tsx`):** big "Describe your idea" text box, a Go button that navigates to `/results?idea=<encoded>`, and 3 example ideas as one-click chips (role 4 supplies the final three; use placeholders until then).
2. **Cards:** five cards in a fixed order (Can it be built? · Who wants it? · Features to borrow · Who tried and failed · Who to talk to). Each shows a skeleton until its `card` event arrives, then the summary and claims. After each claim, numbered `SourceChip`s that open the source URL in a new tab. Sources come from `evidence` events; look up by `sourceId`.
3. **Demo replay (`lib/replay.ts`):** `?demo=<slug>` on the results page replays `public/demo/<slug>.json` (a `DemoRun`) with its original timing instead of calling the API. Export something like `replayDemo(slug): AsyncGenerator<ExploreEvent>`; role 2 calls it from the results page when `demo` is set.

**Build against fake data now:** `public/demo/fixture.json`, or `POST /api/explore` (streams the fixture). Role 1 swaps in the real pipeline later; the format stays the same.

**Done when (~1:45):** home → results works, and all five cards fill in from the fixture with clickable source chips. Then build demo replay and help record 2–3 real runs once role 1's pipeline works. Merge to `main` when it works, and post on the OpenCrawl board.

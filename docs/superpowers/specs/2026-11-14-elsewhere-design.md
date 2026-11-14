# Elsewhere: design

**Date:** 2026-11-14 · **Event:** Ground Truth hackathon (You.com) · **Freeze:** 3:15 PM ET · **Devpost closes:** 4:00 PM ET sharp

## Why

Founders get stuck inside their own industry. Most ideas aren't new: someone, somewhere, has solved a version of the same problem, often in a field you would never think to look at. Elsewhere takes an idea, reduces it to its core concept, and finds where that concept already lives in *other* industries. Then it tells you whether the idea can really be built, who actually wants it, what features to borrow, who tried and failed, and who you could work with.

- **User:** a founder (or would-be founder) in the ideation phase, before they commit to building.
- **Track:** The Analyst. One profession (founders), a research memo in minutes instead of weeks, every claim cited.
- **Who pays:** *open, team to decide before the pitch.* Early founders rarely pay; likely payers are accelerators, startup studios, university venture programs or corporate innovation teams that screen many ideas.

## What the user gets (the five results)

For one idea, Elsewhere returns a cross-industry map plus five cards, every claim linked to a source it actually read:

1. **Can it be built?** Where the same core concept already works, in any industry. That's the evidence it's doable.
2. **Who wants it?** Real people describing this pain, mostly Reddit threads, with quotes and links.
3. **Features to borrow.** What analogous products in other industries do that this idea could add.
4. **Who tried and failed.** Shut-down startups with a similar concept and why they died.
5. **Who to talk to.** Companies, organizations and public founders working on the concept in other industries, as potential collaborators.

## Goals, non-goals, anti-goals

**Goals**
- Type an idea → the map starts filling in within ~5 s, and all five cards finish within ~60 s.
- Visually striking: an animated map with the idea in the center and industries linked around it, filling in live.
- Every claim cited. You.com does all the searching and reading, and its model service does the reasoning.
- A **demo mode** that replays saved runs, so the live demo never depends on API latency or Wi-Fi.

**Non-goals (today)**
- Accounts, login, saved history, database.
- Payments (XDC AI) and extra data providers (Treg). Add one only if it fills a real gap later.
- Mobile polish beyond "doesn't break."

**Anti-goals (a failure even if it runs)**
- A claim or company name that doesn't come from a source we retrieved. We filter out any claim whose cited source wasn't actually fetched.
- Collecting personal contact details (emails, phone numbers) for "who to talk to." Only organizations and public figures, linked to public pages.
- A blank screen while waiting. Something must appear within seconds.
- The You.com key reaching the browser.

## Constraints

- About 3 hours of build time, 3 people, one branch each (`naman`, plus one per teammate), merged into `main` when ready.
- Public repo: secrets only in `.env.local` (gitignored). `.env.example` is committed with names only.
- TypeScript throughout.
- Must use You.com (core) and OpenCrawl (team's coding agents coordinate through the OpenCrawl board).

## Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| **A** | Next.js app; our own pipeline: model abstracts the idea → parallel You.com searches → read the best pages → model writes cards | Most code, but full control of speed, sources and visuals | **Picked** |
| B | Same app, but each card is one You.com Research API call with structured output | Less glue code, but tens of seconds per call, less source control, higher cost, and in testing "lite" confused same-named products | Used **only** for card 5 (who to talk to) |
| C | Python backend + Streamlit page | Fast for Python teams, but can't deliver the interactive map; looks like a dashboard | Rejected (team writes TypeScript; visuals matter) |

## How it works

**Stack:** Next.js (App Router) + TypeScript + Tailwind. Map: `react-force-graph-2d`. Runs locally for the demo; deploying to Vercel is optional.

**You.com services used**
- **Inference Router** (`https://api.you.com/v1/chat/completions`, OpenAI-compatible, `Authorization: Bearer $YDC_API_KEY`): the reasoning model. Start with `deepseek-v4.1-flash` (fast, cheap, structured output). Fall back to `glm-5.3` if quality is weak. Confirm both via `GET /v1/models` once the key is in.
- **Web Search** (`POST https://ydc-index.io/v1/search`, header `X-API-Key`): `extraction: {extraction_mode: "highlights"}`, count ~5 per query.
- **Contents** (`POST https://ydc-index.io/v1/contents`): full markdown for the few best pages per card.
- **Research** (`POST https://api.you.com/v1/research`): card 5 only, `research_effort: "standard"` with `output_schema`.

**Pipeline (`POST /api/explore`, streams newline-delimited JSON events)**

1. **Abstract** (model, JSON output): from the idea, produce the core concept in plain words, the original industry, and 5 *other* industries where the concept could apply. Each industry gets a one-line "why" and 1–2 search queries. Also produce queries for demand (Reddit) and failures.
   → emits `concept`, then one `industry` event per industry (the map nodes appear).
2. **Search fan-out** (all in parallel):
   - per industry: "where this concept already works" queries → evidence for card 1 and card 3
   - demand: `site:reddit.com` queries → card 2
   - failures: queries boosted toward failure databases (e.g. `failory.com`, `cbinsights.com`, `ideaproof.io`, `failed-startups.com`) → card 4
   - card 5: start the Research API call right after step 1, polled in parallel with everything else
   → emits `evidence` events as results land (the map's industry nodes light up).
3. **Read:** Contents API on the top 2–3 URLs per card (highlights alone are fine for anything else).
4. **Write cards** (model, JSON output, one call per card, in parallel): each claim lists the source IDs it relies on. **Citation guard:** drop any claim citing a source ID we didn't retrieve.
   → emits `card` events as each finishes, then `done`.

**Event contract (`lib/types.ts`, shared by front end and back end)**

```ts
type Source   = { id: string; url: string; title: string; snippet?: string };
type Industry = { id: string; name: string; why: string };
type Claim    = { text: string; sourceIds: string[] };
type Card     = {
  kind: "feasibility" | "demand" | "features" | "failures" | "collaborators";
  title: string;
  summary: string;
  claims: Claim[];
};
type ExploreEvent =
  | { type: "concept";  concept: string; originalIndustry: string }
  | { type: "industry"; industry: Industry }
  | { type: "evidence"; industryId: string | null; sources: Source[] }
  | { type: "card";     card: Card }
  | { type: "error";    stage: string; message: string }
  | { type: "done" };
```

**Screens**
- **Home:** one large text box ("Describe your idea"), a Go button, and 3 example ideas as one-click chips.
- **Results:** the idea at the center of the map with industry nodes animating in as events arrive. Clicking a node opens a side panel with its evidence. Below the map are the five cards, each claim followed by numbered source chips that open the page.

**Demo mode:** `?demo=<slug>` replays a recorded event stream from `public/demo/<slug>.json` with its original timing. We record 2–3 good live runs before 3 PM. The fixture also lets the UI be built before the pipeline works.

## Suggested split (team to confirm)

Each person owns separate files, so merging into `main` rarely conflicts:

| Owner | Files | First deliverable |
|---|---|---|
| Pipeline | `lib/you.ts`, `lib/llm.ts`, `lib/pipeline.ts`, `app/api/explore/route.ts` | Abstract step + one search card streaming end to end |
| UI | `app/page.tsx`, `app/results/*`, `components/*` | Map + cards rendering from a fake event fixture |
| Pitch | `public/demo/*`, `README.md`, Devpost text, slides | 3 strong example ideas, "who pays" answer, OpenCrawl story |

`lib/types.ts` (the contract above) and the Next.js scaffold land on `main` first, so everyone branches from the same base.

## Calls made while writing this (check these)

- Card 5's Research API sources count as "retrieved" for the citation guard. If it hasn't finished when the other four are done, card 5 shows "still researching" and fills in when ready. It doesn't block `done`.
- Model output uses the Inference Router's structured-output mode (JSON schema). If a model rejects it, we fall back to "reply in JSON" in the prompt plus parsing.
- The demo runs on a laptop at `localhost`. Vercel only if time allows.

## Left to the builder

Exact prompts, query counts, model choice after testing, styling and animation details, error and retry handling, and whether a card falls back to highlights when Contents is slow.

## Open items (team)

- `YDC_API_KEY` from the organizers' free credits → `.env.local`.
- Who owns which part.
- Who pays, and how much (for the pitch).
- OpenCrawl beyond team coordination, for the "Best use of OpenCrawl" prize (optional).

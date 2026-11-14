# Elsewhere Shared Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put a runnable Next.js base on `main` that all four teammates branch from: the shared event contract, a fake event stream the UI owners can build against, and a stub API that streams it.

**Architecture:** One Next.js App Router project at the repo root. `lib/types.ts` is the contract between the pipeline (role 1) and the UI (roles 2–3). A stub `POST /api/explore` streams `public/demo/fixture.json` as newline-delimited JSON, using the same wire format the real pipeline will use, so UI work never waits on the pipeline.

**Tech Stack:** Next.js (latest, App Router, TypeScript, Tailwind, ESLint, npm), `react-force-graph-2d`, `zod`, `vitest`.

**Spec:** `docs/superpowers/specs/2026-11-14-elsewhere-design.md`

## Global Constraints

- Repo is public: no secrets in any committed file. Keys live only in `.env.local` (already gitignored via `.env.*`); `.env.example` holds names only.
- Env var names: `YDC_API_KEY`.
- TypeScript strict mode (create-next-app default).
- Project at the repo root (no `src/` dir), import alias `@/*`.
- The fixture is clearly fake: source URLs are `https://example.com/...`, titles start with "Sample". No real company names presented as findings.
- Don't touch `.claude/`, `CLAUDE.local.md`, or `.gitignore` entries that already exist (append only).

## Review Focus

1. **NDJSON split across chunks:** a network chunk can end mid-line; `readEvents` must buffer and only parse complete lines. Test: feed one event split across two chunks → yields exactly one event.
2. **Trailing line without newline:** the last event may arrive without `\n`. Test: stream ending in `{"type":"done"}` with no newline → still yields `done`.
3. **Fixture citation integrity:** every `sourceId` cited in a fixture card must exist in some fixture `evidence` event (the citation guard's invariant). Test in fixture test.
4. **Unknown event type from the server:** `readEvents` must skip a line that fails `ExploreEventSchema` rather than throw. Test: stream with one bad line between two good ones → yields two events.
5. **Secrets in the base commit:** `git ls-files` after Task 3 must not list `.env.local` or anything under `.claude/`. Verification step in Task 3.

---

### Task 1: Next.js scaffold

**Files:**
- Create: Next.js project files at repo root (`package.json`, `app/*`, `next.config.*`, `tsconfig.json`, `eslint.config.*`, `postcss.config.*`, `public/*`)
- Modify: `.gitignore` (merge create-next-app's entries with the existing ones: keep every existing line)

**Interfaces:**
- Produces: `npm run dev`, `npm run build`, `npm run lint`, `npm test` (vitest) scripts. Deps installed: `react-force-graph-2d`, `zod`; devDeps: `vitest`.

- [ ] **Step 1:** Scaffold in a temp dir and move into the repo root (create-next-app refuses non-empty dirs): `npx create-next-app@latest <tmp>/elsewhere --ts --tailwind --eslint --app --no-src-dir --import-alias "@/*" --use-npm --yes`, then copy everything except `.git` into the repo root, merging `.gitignore`.
- [ ] **Step 2:** `npm install react-force-graph-2d zod` and `npm install -D vitest`; add `"test": "vitest run"` to scripts.
- [ ] **Step 3:** Replace `app/page.tsx` with a minimal placeholder: heading "Elsewhere", one line "Find where your idea already lives." (role 3 owns this file afterwards). Set `metadata.title` in `app/layout.tsx` to "Elsewhere".
- [ ] **Step 4:** Verify: `npm run build` exits 0 and `npm run lint` exits 0.
- [ ] **Step 5:** Commit: `chore: scaffold Next.js app`.

### Task 2: Event contract, NDJSON reader, fixture

**Files:**
- Create: `lib/types.ts`, `lib/ndjson.ts`, `public/demo/fixture.json`
- Test: `tests/ndjson.test.ts`, `tests/fixture.test.ts`

**Interfaces:**
- Produces (in `lib/types.ts`): the types `Source`, `Industry`, `Claim`, `CardKind`, `Card`, `ExploreEvent` exactly as in the spec's "Event contract", plus
  - `type DemoRun = { slug: string; idea: string; events: { at: number; event: ExploreEvent }[] }` (`at` = ms since start)
  - zod schemas `ExploreEventSchema` and `DemoRunSchema` matching those types (types derived with `z.infer` or kept in sync; either is fine)
  - `const CARD_KINDS = ["feasibility","demand","features","failures","collaborators"] as const`
- Produces (in `lib/ndjson.ts`):
  - `encodeEvent(e: ExploreEvent): string` → `JSON.stringify(e) + "\n"`
  - `async function* readEvents(body: ReadableStream<Uint8Array>): AsyncGenerator<ExploreEvent>`: buffers partial lines, parses each complete line, validates with `ExploreEventSchema`, skips invalid lines, flushes a final unterminated line.

- [ ] **Step 1: Write failing tests** `tests/ndjson.test.ts`:
  - `round-trips events`: encode `[concept, done]` into one stream → `readEvents` yields both, deep-equal.
  - `handles a line split across chunks`: one event's encoding split at its midpoint into 2 chunks → yields exactly 1 event.
  - `flushes a final line without newline`: stream `'{"type":"done"}'` → yields `[{type:"done"}]`.
  - `skips invalid lines`: chunks `concept\n`, `{"type":"nope"}\n`, `done\n` → yields 2 events.
- [ ] **Step 2: Write failing tests** `tests/fixture.test.ts`:
  - `fixture matches DemoRunSchema`: parse `public/demo/fixture.json`.
  - `fixture has the full story`: exactly 1 `concept`, exactly 5 `industry`, ≥5 `evidence`, one `card` per kind in `CARD_KINDS`, last event is `done`.
  - `every cited source exists`: each `card.claims[].sourceIds[]` is the `id` of some `evidence` source.
  - `timestamps ascend`: `at` is non-decreasing and the last `at` ≤ 45000.
  - `fixture is clearly fake`: every source URL starts with `https://example.com/`.
- [ ] **Step 3:** Run `npm test` → both files FAIL (modules/fixture missing).
- [ ] **Step 4:** Implement `lib/types.ts` and `lib/ndjson.ts` per Interfaces.
- [ ] **Step 5:** Write `public/demo/fixture.json`: slug `"fixture"`, idea "A service that lets restaurants sell surplus food to nearby people at a discount before closing". Concept at ~800 ms; 5 industries (e.g. airlines/last-minute seats, hotels/unsold rooms, events/unsold tickets, retail/clearance, energy/off-peak power) every ~600 ms; evidence events per industry plus `industryId: null` evidence for demand/failures; the five cards spread over ~8–40 s with 2–3 claims each citing fixture source ids; `done` last. All sources `https://example.com/...`, titles "Sample: …".
- [ ] **Step 6:** Run `npm test` → all PASS.
- [ ] **Step 7:** Commit: `feat: event contract, NDJSON reader, fake fixture`.

### Task 3: Stub API, env example, README

**Files:**
- Create: `app/api/explore/route.ts`, `.env.example`, `README.md` (replace create-next-app's)

**Interfaces:**
- Consumes: `encodeEvent`, `DemoRunSchema` (Task 2), `public/demo/fixture.json`.
- Produces: `POST /api/explore` with JSON body `{ idea: string }` → `200`, `Content-Type: application/x-ndjson`, streams the fixture's events with their `at` timing (`?fast=1` → no delays). Role 1 replaces the body with the real pipeline; the request/response shape stays.

- [ ] **Step 1:** Implement the route: read and validate the fixture with `DemoRunSchema`, stream via `ReadableStream` + `encodeEvent`, waiting `at` deltas unless `fast=1`; `400` with `{error}` when `idea` is missing/blank. Add `export const dynamic = "force-dynamic"`.
- [ ] **Step 2:** `.env.example`: `YDC_API_KEY=` with a comment pointing to https://you.com/platform/api-keys and saying to copy to `.env.local`.
- [ ] **Step 3:** `README.md`: one-paragraph pitch of Elsewhere; setup (`npm install`, copy `.env.example` → `.env.local`, `npm run dev`); the 4 roles and file ownership table from the spec; branch workflow (own branch, merge to main when ready, pull main often); "build UI against `POST /api/explore` (streams the fake fixture) or `public/demo/fixture.json`".
- [ ] **Step 4: Verify:** `npm run build` exits 0; with `npm run dev` running, `curl -sN -X POST localhost:3000/api/explore?fast=1 -H 'content-type: application/json' -d '{"idea":"x"}' | tail -1` prints `{"type":"done"}`; the same with `-d '{}'` returns HTTP 400; `git ls-files | grep -E '^\.claude/|\.env\.local$'` prints nothing.
- [ ] **Step 5:** Commit: `feat: stub explore API, env example, README`.

### Task 4: Publish the base (controller does this, not a subagent)

- [ ] Merge `naman` into `main` (fast-forward), `git push origin main naman`.
- [ ] Post on the OpenCrawl board: base is on `main`, how to start (pull, `npm install`, `.env.local`), roles 1–4, `lib/types.ts` is the shared contract and changes to it must be announced on the board.

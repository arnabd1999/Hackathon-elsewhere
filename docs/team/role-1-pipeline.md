# Role 1: Pipeline (Claude Max, Fable 5.2)

Paste this into your coding agent.

---

You're building the search-and-reasoning pipeline for **Elsewhere**, a hackathon app: a founder types an idea, and we find where its core concept already lives in other industries, then return five cited cards. Read `docs/superpowers/specs/2026-11-14-elsewhere-design.md` (sections "How it works" and "Event contract") before writing code. `lib/types.ts` and `lib/ndjson.ts` already exist; use them, and don't change `lib/types.ts` without telling the team.

**You own:** `lib/you.ts`, `lib/llm.ts`, `lib/pipeline.ts`, `lib/prompts.ts`, `app/api/explore/route.ts` (currently a stub streaming the fake fixture; replace its body, keep the request/response shape: `POST {idea}` → `application/x-ndjson` stream of `ExploreEvent`s).

**You.com (key in `.env.local` as `YDC_API_KEY`, server-side only):**
- Model: `POST https://api.you.com/v1/chat/completions` (OpenAI-compatible), header `Authorization: Bearer $YDC_API_KEY`. Start with `deepseek-v4.1-flash`, fall back to `glm-5.3`. Check `GET https://api.you.com/v1/models` first. Use structured JSON output; if refused, ask for JSON in the prompt and parse.
- Search: `POST https://ydc-index.io/v1/search`, header `X-API-Key`, body `{query, count: 5, extraction: {extraction_mode: "highlights"}}`. Supports `site:` in the query, `include_domains`, `boost_domains`, `freshness`.
- Contents: `POST https://ydc-index.io/v1/contents`, header `X-API-Key`, `{urls: [...], formats: ["markdown"]}`.
- Research (card 5 only): `POST https://api.you.com/v1/research` with `research_effort: "standard"` and an `output_schema`. Note: Inference Router / Research / Answer live on `api.you.com`; sending them to `ydc-index.io` returns 403.
- Verify request/response field names in the docs (`https://you.com/docs/llms.txt`) before relying on them.

**Order (each step demoable):**
1. `lib/you.ts` + `lib/llm.ts`: thin typed clients with timeouts. Smoke-test each from a script.
2. Abstract step → emit `concept`, then 5 `industry` events. **Merge to main as soon as this streams** (~1:45): the map can light up with real data.
3. Search fan-out in parallel → `evidence` events (per industry; `industryId: null` for Reddit demand and failure sources, boosting `failory.com`, `cbinsights.com`, `ideaproof.io`, `failed-startups.com`).
4. Cards (one model call per card, in parallel) → `card` events. **Citation guard:** drop any claim whose `sourceIds` aren't in the sources you actually retrieved.
5. Card 5 via Research API, started right after step 2. Don't block `done` on it for more than ~20 s after the others finish.
6. Errors: emit `{type:"error", stage, message}` and keep going with the other cards. Never expose the key or raw stack traces.

**Done when:** a real idea streams concept + 5 industries within ~5 s and all five cards within ~60 s, every claim citing a retrieved source. Then help role 3 record 2–3 demo runs into `public/demo/<slug>.json` (format `DemoRun` in `lib/types.ts`).

Post on the OpenCrawl board when you merge to `main`.

# Elsewhere

A founder types an idea. Elsewhere finds where its core concept already lives in other industries and returns five cited cards (feasibility, demand, features, failures, collaborators), streamed live and shown on a map. Built for the You.com hackathon with You.com search and OpenCrawl.

## Setup

```bash
npm install
cp .env.example .env.local   # add YDC_API_KEY (names only in .env.example; never commit .env.local)
npm run dev                  # http://localhost:3000
npm test
```

## Team

Roles, file ownership and kickoff steps: [docs/team/README.md](docs/team/README.md).

## Build against fake data

`POST /api/explore` with `{ "idea": "..." }` streams the fake fixture as NDJSON (add `?fast=1` to skip delays). You can also read `public/demo/fixture.json` directly. The event contract lives in `lib/types.ts`; read streams with `readEvents()` from `lib/ndjson.ts`.

## Workflow

Work on your own branch, merge to `main` when a piece works, and pull `main` often.

# Team kickoff: Elsewhere

Read the design first: [`docs/superpowers/specs/2026-11-14-elsewhere-design.md`](../superpowers/specs/2026-11-14-elsewhere-design.md).

**Times (ET):** first deliverable ~1:45 PM · merge working pieces to `main` by ~2:30 · feature freeze **3:15** · Devpost submitted **3:45** · hard close **4:00**.

## Pick your role

| Role | Account | Brief (paste it into your coding agent) |
|---|---|---|
| 1. Pipeline (heavy lifting) | Claude Max (Fable 5.2) | [role-1-pipeline.md](role-1-pipeline.md) |
| 2. The map (the wow) | Claude Pro | [role-2-map.md](role-2-map.md) |
| 3. Home, cards, demo replay | Claude Pro | [role-3-cards.md](role-3-cards.md) |
| 4. Pitch, Devpost, demo ideas | ChatGPT Plus ×2 | [role-4-pitch.md](role-4-pitch.md) |

## Start (everyone)

```bash
git clone https://github.com/arnabd1999/Hackathon-elsewhere.git && cd Hackathon-elsewhere
git checkout -b <your-name>
npm install
cp .env.example .env.local   # paste YDC_API_KEY (role 1 needs it; others optional)
npm run dev                  # http://localhost:3000
```

## Rules

- **Your branch only.** Merge to `main` when a piece works (`git pull origin main` first, then `git checkout main && git merge <you> && git push`), then tell the others.
- **Touch only the files your role owns.** Need something in another role's file? Ask its owner.
- **`lib/types.ts` is the shared contract.** Don't change it without telling everyone (post on the OpenCrawl board too).
- **Never commit `.env.local`** or any key. The repo is public.
- **OpenCrawl:** keep your coding agent registered on the team's OpenCrawl board with your role as its task. Post there when you merge to `main`, change `lib/types.ts`, or are blocked. This is also how we compete for "Best use of OpenCrawl."
- **Build UI against fake data:** `POST /api/explore` streams `public/demo/fixture.json` until role 1 replaces it with the real pipeline. Read events with `readEvents()` from `lib/ndjson.ts`.

import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";
import { DemoRunSchema, CARD_KINDS } from "../lib/types";

const raw = JSON.parse(
  fs.readFileSync(path.join(process.cwd(), "public/demo/fixture.json"), "utf8"),
);

describe("fixture", () => {
  it("fixture matches DemoRunSchema", () => {
    expect(DemoRunSchema.safeParse(raw).success).toBe(true);
  });
  const run = DemoRunSchema.parse(raw);
  const evs = run.events.map((e) => e.event);
  it("fixture has the full story", () => {
    expect(evs.filter((e) => e.type === "concept")).toHaveLength(1);
    expect(evs.filter((e) => e.type === "industry")).toHaveLength(5);
    expect(evs.filter((e) => e.type === "evidence").length).toBeGreaterThanOrEqual(5);
    const kinds = evs.flatMap((e) => (e.type === "card" ? [e.card.kind] : []));
    expect([...kinds].sort()).toEqual([...CARD_KINDS].sort());
    expect(evs[evs.length - 1].type).toBe("done");
  });
  it("every cited source exists", () => {
    const ids = new Set(
      evs.flatMap((e) => (e.type === "evidence" ? e.sources.map((s) => s.id) : [])),
    );
    for (const e of evs)
      if (e.type === "card")
        for (const c of e.card.claims) for (const id of c.sourceIds) expect(ids.has(id)).toBe(true);
  });
  it("timestamps ascend", () => {
    const ats = run.events.map((e) => e.at);
    for (let i = 1; i < ats.length; i++) expect(ats[i]).toBeGreaterThanOrEqual(ats[i - 1]);
    expect(ats[ats.length - 1]).toBeLessThanOrEqual(45000);
  });
  it("fixture is clearly fake", () => {
    for (const e of evs)
      if (e.type === "evidence")
        for (const s of e.sources) expect(s.url.startsWith("https://example.com/")).toBe(true);
  });
});

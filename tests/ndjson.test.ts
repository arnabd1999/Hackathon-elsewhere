import { describe, it, expect } from "vitest";
import { encodeEvent, readEvents } from "../lib/ndjson";
import type { ExploreEvent } from "../lib/types";

const enc = new TextEncoder();
function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(c) {
      for (const ch of chunks) c.enqueue(enc.encode(ch));
      c.close();
    },
  });
}
async function collect(s: ReadableStream<Uint8Array>) {
  const out: ExploreEvent[] = [];
  for await (const e of readEvents(s)) out.push(e);
  return out;
}

const concept: ExploreEvent = { type: "concept", concept: "c", originalIndustry: "i" };
const done: ExploreEvent = { type: "done" };

describe("ndjson", () => {
  it("round-trips events", async () => {
    const out = await collect(streamOf([encodeEvent(concept) + encodeEvent(done)]));
    expect(out).toEqual([concept, done]);
  });
  it("handles a line split across chunks", async () => {
    const s = encodeEvent(concept);
    const mid = Math.floor(s.length / 2);
    const out = await collect(streamOf([s.slice(0, mid), s.slice(mid)]));
    expect(out).toEqual([concept]);
  });
  it("flushes a final line without newline", async () => {
    expect(await collect(streamOf(['{"type":"done"}']))).toEqual([done]);
  });
  it("skips invalid lines", async () => {
    const out = await collect(
      streamOf([encodeEvent(concept), '{"type":"nope"}\n', encodeEvent(done)]),
    );
    expect(out).toHaveLength(2);
  });
});

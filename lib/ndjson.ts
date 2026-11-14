import { ExploreEventSchema, type ExploreEvent } from "./types";

export function encodeEvent(e: ExploreEvent): string {
  return JSON.stringify(e) + "\n";
}

function parseLine(line: string): ExploreEvent | null {
  const trimmed = line.trim();
  if (!trimmed) return null;
  try {
    const parsed = ExploreEventSchema.safeParse(JSON.parse(trimmed));
    return parsed.success ? (parsed.data as ExploreEvent) : null;
  } catch {
    return null;
  }
}

export async function* readEvents(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<ExploreEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let nl: number;
      while ((nl = buffer.indexOf("\n")) >= 0) {
        const ev = parseLine(buffer.slice(0, nl));
        buffer = buffer.slice(nl + 1);
        if (ev) yield ev;
      }
    }
    buffer += decoder.decode();
    const last = parseLine(buffer);
    if (last) yield last;
  } finally {
    reader.releaseLock();
  }
}

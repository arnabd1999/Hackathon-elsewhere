import fs from "fs";
import path from "path";
import { encodeEvent } from "@/lib/ndjson";
import { DemoRunSchema } from "@/lib/types";

// Stub: streams the fake fixture. Role 1 replaces the body with the real pipeline;
// the request/response shape stays.
export async function POST(req: Request) {
  const url = new URL(req.url);
  const fast = url.searchParams.get("fast") === "1";

  let idea = "";
  try {
    const body = await req.json();
    if (typeof body?.idea === "string") idea = body.idea.trim();
  } catch {
    // fall through to 400
  }
  if (!idea) {
    return Response.json({ error: "idea is required" }, { status: 400 });
  }

  const run = DemoRunSchema.parse(
    JSON.parse(
      fs.readFileSync(path.join(process.cwd(), "public/demo/fixture.json"), "utf8"),
    ),
  );

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let prev = 0;
      for (const { at, event } of run.events) {
        if (!fast && at > prev) await new Promise((r) => setTimeout(r, at - prev));
        prev = at;
        controller.enqueue(encoder.encode(encodeEvent(event)));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "application/x-ndjson",
      "Cache-Control": "no-cache, no-transform",
    },
  });
}

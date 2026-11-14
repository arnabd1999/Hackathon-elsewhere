// Elsewhere frontend <-> backend contract.
//
// The UI only talks to the backend through the functions in `API` below.
// While USE_MOCK is true, every call is answered by static/mock.js, so the
// frontend can be built and demoed with no keys and no server-side agent.
//
// BACKEND TEAM: fill in the TODO bodies in `RealAPI`, then flip USE_MOCK to
// false (or open the page with ?live=1). Keep the event shapes documented
// below; the UI depends on them.
// RealAPI is wired to server.py: /api/explore, /api/replay (SSE), /api/demos, /api/deep-dive.
//
// Event shapes (streamed in this order, same as pipeline.py):
//   {type:"stage",   msg}
//   {type:"core",    core_idea, core_mechanism, user_execution:{customer,geography,business_model,technology,channel}, queries:[{lens,label,q}]}
//   {type:"universe", id, name, website, one_liner, kind:"parallel"|"inspiration", industry, transfer,
//                     execution:{...5 axes}, divergent_axes:[...], divergence, divergence_summary,
//                     relationship:"competitor"|"collaborator", relationship_reason, lesson,
//                     evidence_quote, verification:"verified"|"partial"|"unverified",
//                     source_url, source_title, lens, lens_label,
//                     receipt_url? (link that highlights the quote on the page), name_on_page? (bool),
//                     similarity? (optional 0-100; UI derives it from divergence when missing)}
//   {type:"status",  id, status:"thriving"|"active"|"pivoted"|"shut_down"|"quiet"|"unknown",
//                     signal, signal_url, signal_date, conflict}
//   {type:"done",    count}
//   {type:"error",   msg}

const params = new URLSearchParams(location.search);

export const CONFIG = {
  USE_MOCK: params.get("live") !== "1",
  // Mock key only. Real keys live in the backend .env, never in the browser.
  API_KEY: "mock-elsewhere-key-0000",
  BASE_URL: "",
};

// Open an SSE stream and forward parsed events. Returns a cancel function.
// EventSource auto-reconnects on error, so we always close on done/error/onerror
// (a reconnect would silently start a second paid run).
// endIsOk: when the stream closes after >=1 event with no done event (replay), end quietly.
function streamEvents(url, onEvent, endIsOk) {
  const es = new EventSource(url);
  let closed = false, got = false;
  const close = () => { closed = true; es.close(); };
  es.onmessage = m => {
    if (closed) return;
    let ev;
    try { ev = JSON.parse(m.data); } catch { return; }
    got = true;
    if (ev.type === "done" || ev.type === "error") close();
    onEvent(ev);
  };
  es.onerror = () => {
    if (closed) return;
    close();
    if (!(endIsOk && got)) onEvent({ type: "error", msg: "Connection to the server was lost." });
  };
  return close;
}

const RealAPI = {
  /** Start a live run. Call onEvent(ev) for each event; return a function that cancels the run. */
  explore(idea, onEvent) {
    return streamEvents(`${CONFIG.BASE_URL}/api/explore?idea=${encodeURIComponent(idea)}`, onEvent, false);
  },

  /** List recorded runs: [{file, idea}] */
  async listDemos() {
    const r = await fetch(`${CONFIG.BASE_URL}/api/demos`);
    if (!r.ok) throw new Error(`Could not list demos (HTTP ${r.status})`);
    return r.json();
  },

  /** Replay a recorded run with the same event stream as explore(). */
  replay(file, onEvent) {
    return streamEvents(`${CONFIG.BASE_URL}/api/replay?file=${encodeURIComponent(file)}`, onEvent, true);
  },

  /** "Why did this universe die?" deep dive. Resolves to {summary, sources:[{title,url}]} */
  async deepDive(u) {
    const body = {};
    for (const k of ["name", "one_liner", "website", "status", "signal", "industry"]) body[k] = u[k] ?? "";
    const r = await fetch(`${CONFIG.BASE_URL}/api/deep-dive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      let detail = "";
      try { const j = await r.json(); detail = typeof j.detail === "string" ? j.detail : ""; } catch {}
      throw new Error(detail || `Deep dive failed (HTTP ${r.status})`);
    }
    return r.json();
  },
};

async function mockApi() {
  const m = await import("./mock.js");
  return m.MockAPI;
}

export const API = {
  async explore(idea, onEvent) {
    return CONFIG.USE_MOCK ? (await mockApi()).explore(idea, onEvent) : RealAPI.explore(idea, onEvent);
  },
  async listDemos() {
    return CONFIG.USE_MOCK ? (await mockApi()).listDemos() : RealAPI.listDemos();
  },
  async replay(file, onEvent) {
    return CONFIG.USE_MOCK ? (await mockApi()).replay(file, onEvent) : RealAPI.replay(file, onEvent);
  },
  async deepDive(universe) {
    return CONFIG.USE_MOCK ? (await mockApi()).deepDive(universe) : RealAPI.deepDive(universe);
  },
};

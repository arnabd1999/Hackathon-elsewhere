// Elsewhere frontend <-> backend contract.
//
// The UI only talks to the backend through the functions in `API` below.
// While USE_MOCK is true, every call is answered by static/mock.js, so the
// frontend can be built and demoed with no keys and no server-side agent.
//
// BACKEND TEAM: fill in the TODO bodies in `RealAPI`, then flip USE_MOCK to
// false (or open the page with ?live=1). Keep the event shapes documented
// below; the UI depends on them.
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

// Real implementations: intentionally left blank for the backend team.
const RealAPI = {
  /** Start a live run. Call onEvent(ev) for each event; return a function that cancels the run. */
  explore(idea, onEvent) {
    // TODO(backend): stream /api/explore?idea=... (SSE) and forward each parsed event to onEvent.
    // Hint: const es = new EventSource(`${CONFIG.BASE_URL}/api/explore?idea=${encodeURIComponent(idea)}`);
    //       es.onmessage = m => onEvent(JSON.parse(m.data)); return () => es.close();
    onEvent({ type: "error", msg: "Live API not wired yet (RealAPI.explore in static/api.js)." });
    return () => {};
  },

  /** List recorded runs: [{file, idea}] */
  async listDemos() {
    // TODO(backend): return (await fetch(`${CONFIG.BASE_URL}/api/demos`)).json();
    return [];
  },

  /** Replay a recorded run with the same event stream as explore(). */
  replay(file, onEvent) {
    // TODO(backend): stream /api/replay?file=...
    onEvent({ type: "error", msg: "Replay not wired yet (RealAPI.replay in static/api.js)." });
    return () => {};
  },

  /** Stretch: "Why did this universe die?" deep dive. Resolve to {summary, sources:[{title,url}]} */
  async deepDive(universe) {
    // TODO(backend): call a /api/deep-dive endpoint backed by the You.com Research API.
    throw new Error("Deep dive not wired yet (RealAPI.deepDive in static/api.js).");
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

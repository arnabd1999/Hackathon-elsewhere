// Mock backend for frontend work. Every company here is FICTIONAL sample data;
// the UI shows a "Mock data" badge while this file is in use.

const CORE = {
  type: "core",
  core_idea: "Give small shop owners an effortless daily picture of their cash so they stop running out of money.",
  core_mechanism: "Turn messy, informal daily transactions into a simple running balance and an early warning.",
  user_execution: {
    customer: "NYC deli owners",
    geography: "New York City",
    business_model: "monthly subscription",
    technology: "SMS assistant",
    channel: "door-to-door sales",
  },
  queries: [
    { lens: "parallel", label: "Same idea, other execution", q: "app that tracks daily cash for kiosk owners in Kenya" },
    { lens: "parallel", label: "Same idea, other execution", q: "free bookkeeping app for corner shops paid by suppliers" },
    { lens: "parallel", label: "Same idea, other execution", q: "WhatsApp bot cash flow small retailers India" },
    { lens: "parallel", label: "Same idea, other execution", q: "point of sale cash forecasting bodega" },
    { lens: "parallel", label: "Same idea, other execution", q: "voice assistant bookkeeping street vendors" },
    { lens: "cross", label: "Other industry: farming", q: "crop income forecasting app smallholder farmers" },
    { lens: "cross", label: "Other industry: gig work", q: "income smoothing app for rideshare drivers" },
    { lens: "cross", label: "Other industry: healthcare", q: "clinic cash runway dashboard" },
    { lens: "graveyard", label: "Startup graveyard", q: "site:failory.com small business bookkeeping startup failed" },
    { lens: "reddit", label: "Reddit", q: "site:reddit.com deli owner how do you track cash" },
    { lens: "launches", label: "Product Hunt", q: "site:producthunt.com cash flow small shop" },
  ],
};

const U = (o) => ({
  kind: "parallel", website: "", transfer: "", industry: "Small retail", lens: "parallel", lens_label: "Same idea, other execution",
  source_title: "Example source page", verification: "verified", relationship: "collaborator",
  stage: "unknown", funding: "", ticker: "", stage_url: "", unknown_axes: [], ...o,
  divergence: o.divergent_axes.length,   // unknown_axes are NOT counted here
});

const UNIVERSES = [
  U({ id: "m01", name: "Ledgerly", one_liner: "SMS cash log for bodega owners across Chicago.",
      execution: { customer: "bodega owners", geography: "Chicago", business_model: "monthly subscription", technology: "SMS assistant", channel: "door-to-door sales" },
      divergent_axes: ["geography"], divergence_summary: "Same idea, but in Chicago instead of New York.",
      relationship: "collaborator", relationship_reason: "Different city, so no customer overlap; they could license the playbook.",
      lesson: "They hit 400 shops by training one local rep per neighbourhood instead of a big sales team.",
      evidence_quote: "Text us your sales at closing time and we'll text back how much cash you really have.",
      source_url: "https://example.com/ledgerly", source_title: "Ledgerly — cash by text",
      stage: "seed", funding: "$2.1M seed", stage_url: "https://example.com/ledgerly-seed" }),
  U({ id: "m02", name: "TillTalk", one_liner: "Voice-note bookkeeping for NYC delis, read back every morning.",
      execution: { customer: "NYC deli owners", geography: "New York City", business_model: "monthly subscription", technology: "voice notes", channel: "door-to-door sales" },
      divergent_axes: ["technology"], divergence_summary: "Same idea and same customers, but voice notes instead of SMS.",
      relationship: "competitor", relationship_reason: "Same customer in the same city: a direct competitor.",
      lesson: "Owners preferred talking over typing at 11pm; voice doubled daily logging.",
      evidence_quote: "Owners just leave a voice note after closing and TillTalk does the bookkeeping.",
      source_url: "https://example.com/tilltalk", source_title: "TillTalk launch on Product Hunt", lens: "launches", lens_label: "Product Hunt" }),
  U({ id: "m03", name: "DukaBook", one_liner: "Free cash ledger app for kiosk owners in Nairobi, paid for by suppliers.",
      execution: { customer: "kiosk owners", geography: "Kenya", business_model: "supplier-funded, free to shops", technology: "Android app", channel: "supplier reps" },
      divergent_axes: ["geography", "business_model", "technology", "channel"], divergence_summary: "Same idea, but free to shops in Kenya, paid by the wholesalers who supply them.",
      relationship: "collaborator", relationship_reason: "Different continent; their supplier-funded model could be borrowed.",
      lesson: "Getting suppliers to pay removed the shop owner's price objection entirely.",
      evidence_quote: "DukaBook is free for every duka because distributors pay to see demand.",
      source_url: "https://example.com/dukabook", stage: "series_a", funding: "$12M Series A" }),
  U({ id: "m04", name: "CornerCash", one_liner: "Cash forecasting add-on for corner-shop POS systems in London.",
      execution: { customer: "corner shops", geography: "London", business_model: "per-terminal fee", technology: "POS integration", channel: "POS resellers" },
      divergent_axes: ["geography", "technology", "channel"], unknown_axes: ["business_model"], divergence_summary: "Same idea, but plugged into the till instead of asking owners to report.",
      relationship: "collaborator", relationship_reason: "UK market only.", verification: "partial",
      lesson: "Zero data entry wins, but only shops with a modern POS could use it.",
      evidence_quote: "CornerCash reads your till and warns you a week before cash runs short.",
      source_url: "https://example.com/cornercash", stage: "bootstrapped" }),
  U({ id: "m05", name: "Kirana Khata", one_liner: "WhatsApp bot that keeps a credit-and-cash book for Indian grocery stores.",
      execution: { customer: "kirana stores", geography: "India", business_model: "freemium", technology: "WhatsApp bot", channel: "word of mouth" },
      divergent_axes: ["geography", "business_model", "channel", "technology"], divergence_summary: "Same idea, but on WhatsApp in India and spread by word of mouth.",
      relationship: "collaborator", relationship_reason: "Non-overlapping market with a proven chat-based flow.",
      lesson: "Tracking customer credit, not just cash, was what made owners open it daily.",
      evidence_quote: "Shopkeepers send a message for every udhaar sale and Khata keeps the balance.",
      source_url: "https://example.com/kirana-khata", lens: "reddit", lens_label: "Reddit" }),
  U({ id: "m06", name: "BodegaBrain", one_liner: "SMS cash tracker for NYC delis, sold through beverage distributors.",
      execution: { customer: "NYC deli owners", geography: "New York City", business_model: "monthly subscription", technology: "SMS assistant", channel: "distributor partnerships" },
      divergent_axes: ["channel"], divergence_summary: "Almost identical, but sold through the soda distributors who already visit every deli.",
      relationship: "competitor", relationship_reason: "Same customer, same city, same product.",
      lesson: "Distributors already visit every deli weekly: free distribution.",
      evidence_quote: "BodegaBrain rides along with the distributors who already stop at every deli each week.",
      source_url: "https://example.com/bodegabrain" }),
  U({ id: "m07", name: "Shoebox", one_liner: "Receipt-photo cash tracker for US food trucks.",
      execution: { customer: "food truck owners", geography: "United States", business_model: "monthly subscription", technology: "photo receipts", channel: "app store" },
      divergent_axes: ["customer", "geography", "technology"], divergence_summary: "Same idea, but for food trucks nationwide using receipt photos.",
      relationship: "collaborator", relationship_reason: "Different customer segment.",
      lesson: "Self-serve signup worked, but churn was 12% a month without a human touch.",
      evidence_quote: "Snap your receipts and Shoebox tells you if you can afford tomorrow's stock.",
      source_url: "https://example.com/shoebox", lens: "graveyard", lens_label: "Startup graveyard",
      stage: "shut_down", funding: "$800K pre-seed" }),
  U({ id: "m08", name: "Tally Street", one_liner: "Paper-ledger-to-app service for Lagos market traders.",
      execution: { customer: "market traders", geography: "Nigeria", business_model: "transaction fee", technology: "USSD", channel: "market associations" },
      divergent_axes: ["customer", "geography", "technology"], unknown_axes: ["business_model", "channel"], divergence_summary: "Same core idea, but different customers, country and technology.",
      relationship: "collaborator", relationship_reason: "Completely different market.", verification: "unverified",
      lesson: "Working through market associations built trust faster than ads.",
      evidence_quote: "Tally Street turns every trader's notebook into a live balance.",
      source_url: "https://example.com/tally-street", lens: "graveyard", lens_label: "Startup graveyard" }),
  // Other industries, same core mechanism
  U({ id: "m09", name: "HarvestFlow", kind: "inspiration", industry: "Farming", one_liner: "Seasonal income forecasting by SMS for smallholder farmers.",
      transfer: "Their 'lean week' SMS warning, sent 10 days before cash runs out.",
      execution: { customer: "smallholder farmers", geography: "East Africa", business_model: "co-op license", technology: "SMS", channel: "farmer co-ops" },
      divergent_axes: ["customer", "geography", "business_model", "channel"], divergence_summary: "Same mechanism applied to farm income instead of shop cash.",
      relationship_reason: "Different industry; their warning model transfers directly.",
      lesson: "A single proactive warning beat a full dashboard nobody opened.",
      evidence_quote: "HarvestFlow texts farmers ten days before their money is likely to run out.",
      source_url: "https://example.com/harvestflow", lens: "cross", lens_label: "Other industry: farming" }),
  U({ id: "m10", name: "Steady Gig", kind: "inspiration", industry: "Gig work", one_liner: "Income-smoothing app that tells rideshare drivers what's safe to spend.",
      transfer: "The 'safe to spend today' single number instead of a ledger.",
      execution: { customer: "rideshare drivers", geography: "United States", business_model: "freemium", technology: "bank-linked app", channel: "app store" },
      divergent_axes: ["customer", "geography", "technology", "channel"], divergence_summary: "Same mechanism for drivers' volatile daily income.",
      relationship_reason: "Different industry.",
      lesson: "One number ('safe to spend') was the feature everyone remembered.",
      evidence_quote: "Steady Gig shows one number every morning: what is safe to spend today.",
      source_url: "https://example.com/steadygig", lens: "cross", lens_label: "Other industry: gig work",
      stage: "public", ticker: "NASDAQ:STDY", stage_url: "https://example.com/steadygig-ipo" }),
  U({ id: "m11", name: "ClinicRunway", kind: "inspiration", industry: "Healthcare", one_liner: "Cash runway alerts for independent dental clinics.",
      transfer: "Weekly owner digest that turns insurance delays into a cash forecast.",
      execution: { customer: "dental clinic owners", geography: "United States", business_model: "SaaS", technology: "accounting integration", channel: "dental associations" },
      divergent_axes: ["customer", "geography", "business_model", "technology", "channel"], divergence_summary: "Same mechanism for clinics waiting on insurance payouts.",
      relationship_reason: "Different industry.", verification: "partial",
      lesson: "Selling through professional associations cut acquisition cost by two thirds.",
      evidence_quote: "ClinicRunway warns owners weeks before insurance delays turn into a cash crunch.",
      source_url: "https://example.com/clinicrunway", lens: "cross", lens_label: "Other industry: healthcare" }),
  U({ id: "m12", name: "PourCount", kind: "inspiration", industry: "Hospitality", one_liner: "End-of-night text summary of takings for small bars.",
      transfer: "The closing-time ritual: one text at last call.",
      execution: { customer: "bar owners", geography: "Ireland", business_model: "monthly subscription", technology: "SMS", channel: "brewery partners" },
      divergent_axes: ["customer", "geography", "channel"], divergence_summary: "Same mechanism for pubs, timed to last orders.",
      relationship_reason: "Different industry; brewery channel mirrors your distributor angle.",
      lesson: "Brewery reps bundled it into supply contracts: instant distribution.",
      evidence_quote: "At last orders, PourCount texts the landlord exactly what the night took.",
      source_url: "https://example.com/pourcount", lens: "cross", lens_label: "Other industry: hospitality",
      stage: "pre_seed", funding: "€400K pre-seed" }),
];

// event_date = when it happened (YYYY-MM), source_date = when the source was published (YYYY-MM-DD).
// Status events may override stage/funding/ticker/stage_url from the universe event.
const STATUSES = {
  m01: { status: "thriving", signal: "Raised a seed round and expanded to Milwaukee.", event_date: "2026-04", source_date: "2026-09-02" },
  m02: { status: "active", signal: "Launched Spanish-language voice notes.", event_date: "2026-06", source_date: "2026-06-18",
         stage: "seed", funding: "$1.5M seed" },
  m03: { status: "thriving", signal: "Signed a nationwide deal with a major distributor.", event_date: "", source_date: "2026-08-11" },
  m04: { status: "pivoted", signal: "Pivoted to selling forecasts to POS vendors.", event_date: "2026-03", source_date: "" },
  m05: { status: "active", signal: "Passed 1M monthly messages.", event_date: "2026-05", source_date: "2026-05-20" },
  m06: { status: "quiet", signal: "", event_date: "", source_date: "" },
  m07: { status: "shut_down", signal: "Shut down; founders cited churn without in-person support.", event_date: "2025-04", source_date: "2025-11-03",
         conflict: "One directory still lists it as active." },
  m08: { status: "unknown", signal: "", event_date: "", source_date: "" },
  m09: { status: "thriving", signal: "Expanded to three new countries.", event_date: "2026-10", source_date: "2026-10-15" },
  m10: { status: "active", signal: "Launched a debit card.", event_date: "2026-04", source_date: "2026-04-09" },
  m11: { status: "shut_down", signal: "Acquired and wound down.", event_date: "2025-12", source_date: "2026-01-14", stage: "acquired",
         stage_url: "https://example.com/clinicrunway-acquired" },
  m12: { status: "active", signal: "Added Guinness distributor partnership.", event_date: "2026-07", source_date: "2026-07-30" },
};

const ANALYSIS = {
  type: "analysis", market: "emerging", funded: 4, dead: 2,
  summary: "A handful of funded teams are proving demand for daily cash tracking, but nobody owns NYC delis yet. The ones that died relied on self-serve signup, so plan for an in-person or distributor channel from day one.",
};

function stream(events, onEvent, speed = 1) {
  let cancelled = false;
  (async () => {
    for (const [delay, ev] of events) {
      await new Promise((r) => setTimeout(r, delay / speed));
      if (cancelled) return;
      onEvent(ev);
    }
  })();
  return () => { cancelled = true; };
}

function script(idea) {
  const ev = [
    [300, { type: "stage", msg: "Stripping your idea down to its core…" }],
    [900, idea ? { ...CORE, idea } : CORE],
    [500, { type: "stage", msg: `Searching the live web: ${CORE.queries.length} searches across your industry, other industries, graveyards, Reddit and launches…` }],
    [1100, { type: "stage", msg: "Reading 14 source pages…" }],
    [800, { type: "stage", msg: "Extracting companies and checking every quote against its source…" }],
  ];
  UNIVERSES.forEach((u) => ev.push([450 + Math.random() * 400, { type: "universe", ...u }]));
  ev.push([400, { type: "stage", msg: "Checking which universes are still alive today…" }]);
  UNIVERSES.forEach((u) => {
    const s = STATUSES[u.id];
    ev.push([220, { type: "status", id: u.id, conflict: "", signal_url: s.signal ? `https://example.com/news/${u.id}` : null, signal_date: s.source_date, ...s }]);
  });
  ev.push([300, { type: "stage", msg: "Sizing up the market…" }]);
  ev.push([500, ANALYSIS]);
  ev.push([200, { type: "done", count: UNIVERSES.length }]);
  return ev;
}

export const MockAPI = {
  explore: (idea, onEvent) => stream(script(idea), onEvent),
  listDemos: async () => [{ file: "mock-deli-cashflow", idea: "An SMS assistant that helps NYC deli owners track daily cash flow" }],
  replay: (file, onEvent) => stream(script(), onEvent, 1.6),
  deepDive: async (u) => {
    await new Promise((r) => setTimeout(r, 1200));
    return {
      summary: `Mock deep dive for ${u.name}: ${u.lesson}`,
      sources: [{ title: "Example post-mortem", url: "https://example.com/post-mortem" }],
    };
  },
};

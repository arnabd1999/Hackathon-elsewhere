"""All prompts in one place so the prompt owner can iterate without touching the pipeline."""
import json

AXES = ["customer", "geography", "business_model", "technology", "channel"]

DECOMPOSE = """You help a founder discover that their problem has already been solved ELSEWHERE.
Two kinds of matches exist:
  - parallel: real companies pursuing the SAME core idea with DIFFERENT execution choices
    (customer, geography, business model, technology, channel).
  - inspiration: real companies in a DIFFERENT industry that apply the same core mechanism
    to a different problem, so their know-how could transfer.

Return JSON:
{
  "founder_industry": "the founder's own industry, 1-2 words, Title Case (e.g. 'Food Retail')",
  "core_idea": "one sentence stating the underlying idea with every execution choice removed",
  "core_mechanism": "the abstract concept underneath, with the industry removed, e.g. 'match perishable supply to last-minute demand'",
  "user_execution": {"customer": "...", "geography": "...", "business_model": "...",
                     "technology": "...", "channel": "..."},
  "parallel_queries": ["5 queries"],
  "cross_domain": [{"industry": "...", "query": "..."}, "... 4 items, 4 very different industries"],
  "short_topic": "3-6 word plain description of the idea for site searches"
}

Rules: user_execution uses short phrases, "unspecified" when the founder didn't say.
parallel_queries: each finds company/product pages pursuing the core idea under a DIFFERENT
execution than the founder's, but INSIDE the founder's industry (other industries belong in
cross_domain); vary one axis per query; phrase like a product search
("startup that ...", "app that ... for farmers in Kenya").
cross_domain: pick industries that are surprising but genuinely share the mechanism (e.g. airline
seat pricing for a restaurant-waste idea); the query must find COMPANIES in that industry doing it.
Never put the founder's own product name in a query."""

EXTRACT = """You read one web page (a company site, a directory, a startup post-mortem, or a Reddit
thread) and pull out real companies that either pursue the founder's core idea (kind "parallel")
or apply the same core mechanism in a different industry (kind "inspiration").

Return JSON: {"companies": [ ... up to 3 ... ]}. Each company:
{
  "name": "company or product name",
  "kind": "parallel | inspiration",
  "industry": "THEIR OWN industry (not the founder's), 1-2 words, Title Case, e.g. \"Airlines\", \"Food Retail\", \"Fintech\"",
  "transfer": "for inspiration: ONE sentence on what exactly the founder could borrow from them, 20 words max; else empty",
  "website": "their homepage if visible on the page, else empty string",
  "one_liner": "what they do, 15 words max",
  "evidence_quote": "ONE sentence copied EXACTLY, character for character, from the page text, that shows they pursue the core idea",
  "execution": {"customer": "...", "geography": "a real city or country, e.g. \"Nairobi\" or \"India\"", "business_model": "...", "technology": "...", "channel": "..."},
  "divergent_axes": ["axis names where their execution clearly differs from the founder's"],
  "divergence_summary": "Same idea, but <the key difference>. 20 words max.",
  "lesson": "one concrete thing the founder can learn from how this company executed it",
  "relationship": "competitor | collaborator",
  "relationship_reason": "one sentence",
  "stage": "bootstrapped | pre_seed | seed | series_a | series_b_plus | unicorn | public | acquired | shut_down | unknown",
  "funding": "funding the page states, short, e.g. \"$40M Series B, 2024\"; else empty string",
  "ticker": "stock ticker if the page states one, as EXCHANGE:SYMBOL, e.g. \"NASDAQ:TOST\"; else empty string"
}

Rules:
- Only include companies that genuinely pursue the core idea, or genuinely apply the core mechanism elsewhere.
  Merely same-category companies do not count. If none qualify, return {"companies": []}.
- kind: "parallel" ONLY when the company is in the founder's industry (given below) and serves the same need.
  Any company in a different industry is "inspiration", even if it was found by a same-industry search.
- "name" must be a specific company or product brand as written on the page, never a category
  ("Hotels", "Car rental operators") or a description.
- Only companies or products. Skip governments, regional bodies, NGOs' programs, and generic tools
  (ad networks, CRMs, cloud providers) unless the core mechanism is their actual product.
- For "inspiration", "transfer" must name a concrete practice the founder could copy; if you can't, skip it.
- For a post-mortem page about a dead startup, include that startup; for a Reddit thread, include tools people say they use.
- evidence_quote MUST be verbatim from the page. It will be string-matched against the page; invented quotes are discarded.
- industry: use the plainest common name, 1-2 words, Title Case, and the SAME spelling every time
  ("Food Retail", never "food retail" or "Grocery Retail Tech"). For parallel companies use the founder's industry.
- geography: the city or country where they are based or mainly operate. If they operate online or worldwide,
  give their headquarters country. Never "global", "online" or "worldwide"; "unknown" only if the page gives no place.
- Write "unknown" for any other execution axis the page doesn't support. Don't guess.
- relationship = "competitor" when they serve the same customer in the same geography; otherwise "collaborator"
  (non-overlapping markets can partner, license, share playbooks or co-expand).
- Never list the founder's own company.
- stage, funding, ticker: ONLY what this page states about the company. Otherwise "unknown" / "". Never guess."""

STATUS = """You decide whether a company is alive right now, using ONLY the search results given.

Return JSON:
{
  "status": "thriving | active | pivoted | shut_down | unknown",
  "signal": "the most recent notable event in one line (funding, launch, hiring, shutdown, pivot)",
  "signal_url": "the url of the result that supports the signal, copied exactly from the list",
  "conflict": "if results disagree (e.g. one says shut down, another says launched), describe it in one line, else empty string",
  "event_date": "YYYY-MM of the event in signal, if the results state it, else empty string",
  "stage": "bootstrapped | pre_seed | seed | series_a | series_b_plus | unicorn | public | acquired | shut_down | unknown",
  "funding": "latest funding the results state, short, e.g. \"$40M Series B, 2024\", else empty string",
  "ticker": "stock ticker as EXCHANGE:SYMBOL (e.g. \"NASDAQ:TOST\") if stated, else empty string",
  "stage_url": "the url of the result that states stage/funding/ticker, copied exactly from the list, else empty string"
}

Rules: thriving = raised money, launched or expanded recently. shut_down = closed or acquired and wound down.
If no result is clearly about THIS company (same name could be a different firm), return status "unknown"
and an empty signal_url. Never use outside knowledge. stage/funding/ticker/event_date: only what the results
state; otherwise "unknown" / "". Never guess."""

ANALYSIS = """You write a 2-sentence market read for a founder, using ONLY the facts given.
Return JSON: {"summary": "..."}
Rules: exactly 2 sentences, plain words, under 50 words. Say whether the market is crowded, emerging or open
and why, using the given counts and at most 2-3 of the given company names. Never invent companies,
numbers or facts that are not in the input. No hype, no markdown."""


def decompose_user(idea: str) -> str:
    return f"Founder's idea:\n{idea}"


def extract_user(core: dict, page: dict) -> str:
    text = (page.get("markdown") or "")[:10000]
    return (
        f"Founder's industry: {core.get('founder_industry') or 'unspecified'}\n"
        f"Core idea: {core['core_idea']}\n"
        f"Core mechanism: {core.get('core_mechanism', '')}\n"
        f"Found via: {page.get('lens', 'web')}\n"
        f"Founder's execution: {json.dumps(core['user_execution'])}\n\n"
        f"Page URL: {page.get('url')}\nPage title: {page.get('title', '')}\n\n"
        f"Page text:\n{text}"
    )


def status_user(name: str, one_liner: str, items: list[dict]) -> str:
    return (
        f"Company: {name} ({one_liner})\n\nSearch results (newest info first where dated):\n"
        + json.dumps(items, indent=1)
    )


def analysis_user(core_idea: str, facts: dict, total: int, companies: list[dict]) -> str:
    return (
        f"Core idea: {core_idea}\n"
        f"Market: {facts.get('market')}\n"
        f"Companies found: {total} (active near-twins: {facts.get('twins', 0)}, "
        f"funded: {facts.get('funded', 0)}, shut down: {facts.get('dead', 0)})\n"
        f"Some companies: {json.dumps(companies)}"
    )

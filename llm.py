"""Provider-agnostic JSON completion. Set LLM_PROVIDER=openai|anthropic|you.

openai:    OPENAI_API_KEY, optional OPENAI_BASE_URL (any OpenAI-compatible server), LLM_MODEL
anthropic: ANTHROPIC_API_KEY, LLM_MODEL
you:       YDC_API_KEY only. Uses the You.com Research API (effort YOU_LLM_EFFORT, default "lite")
           as the model, for keys without Inference Router credits (the router returns 402).
"""
import json
import os
import re
import httpx

RESEARCH_URL = "https://api.you.com/v1/research"
# Research answers carry citation markers like [[1, 2]] or [1]; they aren't part of the JSON.
_CITATION = re.compile(r"\s*\[\[\s*\d+(?:\s*,\s*\d+)*\s*\]\]|\s*\[\d+(?:\s*,\s*\d+)*\]")


async def _you_research_text(client: httpx.AsyncClient, system: str, user: str,
                             domains: list[str] | None = None) -> str:
    """Runs one prompt through the You.com Research API and returns its text answer.

    Research searches the web on its own; `domains` keeps it on the sites we already read,
    so the facts (and quotes) it uses come from the same pages as our receipts."""
    key = os.getenv("YDC_API_KEY")
    if not key:
        raise RuntimeError("YDC_API_KEY is not set (see .env.example)")
    prompt = (
        f"{system}\n\n"
        "Answer ONLY from the material below; don't search the web unless the task needs it.\n"
        "Reply with a single JSON object only: no prose before or after, no markdown, "
        "no citation markers like [1] or [[1, 2]].\n\n"
        f"{user}"
    )
    body = {"input": prompt, "research_effort": os.getenv("YOU_LLM_EFFORT", "lite")}
    domains = [d for d in (domains or []) if d]
    if domains:
        body["source_control"] = {"include_domains": domains[:20]}
    r = await client.post(
        RESEARCH_URL,
        headers={"X-API-Key": key, "Content-Type": "application/json"},
        json=body,
        timeout=90,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"You.com research (as LLM) {r.status_code}: {r.text[:300]}")
    content = (r.json().get("output") or {}).get("content")
    if isinstance(content, (dict, list)):
        return json.dumps(content)
    return _CITATION.sub("", str(content or ""))


def _parse_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise
        return json.loads(text[start:end + 1])


async def complete_json(client: httpx.AsyncClient, system: str, user: str, max_tokens: int = 2000,
                        domains: list[str] | None = None):
    """`domains` only matters for LLM_PROVIDER=you (see _you_research_text); others ignore it."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "anthropic":
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": os.getenv("LLM_MODEL", "claude-sonnet-5-5"),
                "max_tokens": max_tokens,
                "system": system + "\nRespond with a single JSON object only.",
                "messages": [{"role": "user", "content": user}],
            },
            timeout=90,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Anthropic {r.status_code}: {r.text[:300]}")
        text = "".join(b.get("text", "") for b in r.json()["content"])
    elif provider == "you":
        text = await _you_research_text(client, system, user, domains)
    else:
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={
                "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=90,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:300]}")
        text = r.json()["choices"][0]["message"]["content"]
    return _parse_json(text)

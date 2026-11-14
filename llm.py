"""Provider-agnostic JSON completion. Set LLM_PROVIDER=openai|anthropic.

openai:    OPENAI_API_KEY, optional OPENAI_BASE_URL (any OpenAI-compatible server), LLM_MODEL
anthropic: ANTHROPIC_API_KEY, LLM_MODEL
"""
import json
import os
import re
import httpx


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


async def complete_json(client: httpx.AsyncClient, system: str, user: str, max_tokens: int = 2000):
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

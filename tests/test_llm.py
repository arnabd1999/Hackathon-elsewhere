import asyncio
import json

import httpx

import llm


def test_citation_markers_are_stripped_before_parsing():
    text = '{"a": "x" [[1, 2]], "b": ["y"] [3]}'
    assert llm._parse_json(llm._CITATION.sub("", text)) == {"a": "x", "b": ["y"]}


def test_you_provider_uses_research_and_parses_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "you")
    monkeypatch.setenv("YDC_API_KEY", "test-key")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("X-API-Key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"output": {
            "content": 'Sure: {"ok": true [[1]]}', "content_type": "text",
            "sources": [{"url": "https://a.example", "title": "A", "snippets": ["s1"]}, {"title": "no url"}]}})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return await llm.complete_json(c, "system text", "user text")

    assert asyncio.run(run()) == {"ok": True, "_sources": [{"url": "https://a.example", "title": "A", "snippets": ["s1"]}]}
    assert seen["url"].endswith("/v1/research")
    assert seen["key"] == "test-key"
    assert seen["body"]["research_effort"] == "lite"
    assert "system text" in seen["body"]["input"] and "user text" in seen["body"]["input"]

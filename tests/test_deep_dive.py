import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import server

BODY = {"name": "Acme Foods", "one_liner": "Sells food", "website": "https://acme.example",
        "status": "shut_down", "signal": "Closed in 2023", "industry": "food"}


class DeepDive(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)

    def test_maps_summary_and_sources(self):
        calls = []

        async def fake(client, question, effort="lite"):
            calls.append((question, effort))
            return {"output": {"content": "It failed.", "sources": [
                {"title": "A", "url": "https://a.example"}, {"title": "no url"}, {"url": "https://b.example"}]}}

        with mock.patch.object(server.you, "research", fake):
            r = self.client.post("/api/deep-dive", json=BODY)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"summary": "It failed.", "sources": [
            {"title": "A", "url": "https://a.example"}, {"title": "https://b.example", "url": "https://b.example"}]})
        self.assertIn("Acme Foods", calls[0][0])
        self.assertEqual(calls[0][1], "lite")

    def test_blank_name_rejected_without_research(self):
        fake = mock.AsyncMock()
        with mock.patch.object(server.you, "research", fake):
            for name in ("", "   "):
                r = self.client.post("/api/deep-dive", json={**BODY, "name": name})
                self.assertIn(r.status_code, (400, 422))
        fake.assert_not_called()

    def test_upstream_failure_is_502_without_key(self):
        async def boom(client, question, effort="lite"):
            raise RuntimeError("You.com research failed 500: key=sekrit-key-123")

        with mock.patch.dict(os.environ, {"YDC_API_KEY": "sekrit-key-123"}), \
                mock.patch.object(server.you, "research", boom):
            r = self.client.post("/api/deep-dive", json=BODY)
        self.assertEqual(r.status_code, 502)
        self.assertIn("detail", r.json())
        self.assertNotIn("sekrit-key-123", r.text)


if __name__ == "__main__":
    unittest.main()

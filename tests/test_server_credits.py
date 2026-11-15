"""Out-of-credits handling: a public demo must fail politely and stop spending once You.com says 402."""
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import server


def _never_runs(idea):
    async def gen():
        raise AssertionError("agent must not run")
        yield  # noqa: unreachable, makes this an async generator
    return gen()


async def _out_of_credits(idea):
    yield {"type": "stage", "msg": "Searching"}
    raise RuntimeError('Search returned nothing. You.com search failed 402: {"error":"payment_required",'
                       '"message":"Your prepaid credit balance has been depleted."}')


class OutOfCreditsDetection(unittest.TestCase):
    def test_recognises_you_com_402_messages(self):
        for msg in ("You.com search failed 402: {...}",
                    "You.com research (as LLM) 402: {\"error\":\"payment_required\"}",
                    "Reading pages failed: Your prepaid credit balance has been depleted."):
            self.assertTrue(server.is_out_of_credits(RuntimeError(msg)), msg)

    def test_other_errors_are_not_credit_errors(self):
        for msg in ("You.com search failed 500: oops", "timeout after 4020 ms", "Search returned nothing. "):
            self.assertFalse(server.is_out_of_credits(RuntimeError(msg)), msg)


class Explore(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        server.credit_pause.clear()

    def tearDown(self):
        server.credit_pause.clear()

    def test_live_runs_off_streams_one_friendly_error_without_running_or_using_the_cap(self):
        cap = server.HourlyCap(1)
        with mock.patch.object(server, "LIVE_RUNS_ENABLED", False), \
                mock.patch.object(server, "explore_cap", cap), mock.patch.object(server, "explore", _never_runs):
            r = self.client.get("/api/explore", params={"idea": "x"})
        self.assertIn('"type": "error"', r.text)
        self.assertIn("Replay", r.text)
        self.assertTrue(cap.allow(now=0), "a refused run must not use up a cap slot")

    def test_402_shows_friendly_message_and_pauses_later_runs(self):
        with mock.patch.object(server, "explore", _out_of_credits):
            first = self.client.get("/api/explore", params={"idea": "x"})
        self.assertIn("paused", first.text)
        self.assertNotIn("payment_required", first.text)  # no raw API error for visitors
        self.assertTrue(server.credit_pause.active())

        with mock.patch.object(server, "explore", _never_runs):
            second = self.client.get("/api/explore", params={"idea": "y"})
        self.assertIn("paused", second.text)

    def test_pause_expires(self):
        server.credit_pause.start(now=0)
        self.assertTrue(server.credit_pause.active(now=10))
        self.assertFalse(server.credit_pause.active(now=server.CREDIT_PAUSE_SECONDS + 1))

    def test_other_errors_still_pass_through_and_do_not_pause(self):
        async def broken(idea):
            raise RuntimeError("You.com search failed 500: server error")
            yield  # noqa: unreachable

        with mock.patch.object(server, "explore", broken):
            r = self.client.get("/api/explore", params={"idea": "x"})
        self.assertIn("failed 500", r.text)
        self.assertFalse(server.credit_pause.active())


class DeepDive(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        server.credit_pause.clear()

    def tearDown(self):
        server.credit_pause.clear()

    def test_402_returns_503_with_friendly_detail_and_pauses(self):
        async def broke(client, question, effort="lite"):
            raise RuntimeError("You.com research failed 402: payment_required")

        with mock.patch.object(server.you, "research", broke):
            r = self.client.post("/api/deep-dive", json={"name": "Acme"})
        self.assertEqual(r.status_code, 503)
        self.assertIn("paused", r.json()["detail"])
        self.assertTrue(server.credit_pause.active())

    def test_off_or_paused_never_calls_research(self):
        fake = mock.AsyncMock()
        with mock.patch.object(server.you, "research", fake):
            with mock.patch.object(server, "LIVE_RUNS_ENABLED", False):
                self.assertEqual(self.client.post("/api/deep-dive", json={"name": "Acme"}).status_code, 503)
            server.credit_pause.start()
            self.assertEqual(self.client.post("/api/deep-dive", json={"name": "Acme"}).status_code, 503)
        fake.assert_not_called()


if __name__ == "__main__":
    unittest.main()

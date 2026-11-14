import unittest
from unittest import mock

from fastapi.testclient import TestClient

import server


class Caps(unittest.TestCase):
    def test_hourly_cap_rolls_over(self):
        cap = server.HourlyCap(2)
        self.assertTrue(cap.allow(now=0))
        self.assertTrue(cap.allow(now=10))
        self.assertFalse(cap.allow(now=20))
        self.assertTrue(cap.allow(now=3600))  # first call aged out

    def test_zero_means_unlimited(self):
        cap = server.HourlyCap(0)
        self.assertTrue(all(cap.allow(now=i) for i in range(100)))

    def test_capped_explore_streams_one_error_and_never_runs_the_agent(self):
        client = TestClient(server.app)

        async def boom(idea):
            raise AssertionError("agent must not run when capped")
            yield  # noqa: unreachable, makes this an async generator

        with mock.patch.object(server, "explore_cap", server.HourlyCap(1)), \
                mock.patch.object(server, "explore", boom):
            server.explore_cap.allow()  # use up the only slot
            r = client.get("/api/explore", params={"idea": "x"})
        self.assertEqual(r.status_code, 200)
        self.assertIn('"type": "error"', r.text)
        self.assertIn("hourly limit", r.text)

    def test_capped_deep_dive_is_429(self):
        client = TestClient(server.app)
        with mock.patch.object(server, "deep_dive_cap", server.HourlyCap(1)):
            server.deep_dive_cap.allow()
            r = client.post("/api/deep-dive", json={"name": "Acme"})
        self.assertEqual(r.status_code, 429)


if __name__ == "__main__":
    unittest.main()


class Privacy(unittest.TestCase):
    def test_privacy_event_comes_right_before_done_and_reports_storage(self):
        client = TestClient(server.app)

        async def fake(idea):
            yield {"type": "stage", "msg": "x"}
            yield {"type": "done", "count": 0}

        with mock.patch.object(server, "explore", fake), mock.patch.object(server, "RECORD_RUNS", False):
            r = client.get("/api/explore", params={"idea": "secret idea"})
        types = [line for line in r.text.splitlines() if line.startswith("data:")]
        self.assertIn('"type": "privacy"', types[-2])
        self.assertIn('"stored": false', types[-2])
        self.assertIn('"type": "done"', types[-1])

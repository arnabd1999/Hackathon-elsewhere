import json
import unittest

from fastapi.testclient import TestClient

import server


class ReplaySlug(unittest.TestCase):
    def test_slug_never_ends_with_dash_after_truncation(self):
        idea = "A WhatsApp assistant that gives small corner-shop owners a simple daily picture"
        s = server._slug(idea)
        self.assertLessEqual(len(s), 50)
        self.assertFalse(s.endswith("-"))

    def test_recorded_run_replays_by_its_listed_name(self):
        idea = "zz unit test fixture: replay slug check with a das at char fifty"
        path = server.CACHE / f"{server._slug(idea)}.json"
        path.write_text(json.dumps({"idea": idea, "events": [{"t": 0, "ev": {"type": "done", "count": 0}}]}))
        self.addCleanup(path.unlink)
        client = TestClient(server.app)
        listed = [d["file"] for d in client.get("/api/demos").json()]
        self.assertIn(path.stem, listed)
        r = client.get("/api/replay", params={"file": path.stem})
        self.assertEqual(r.status_code, 200)
        self.assertIn('"type": "done"', r.text)


if __name__ == "__main__":
    unittest.main()

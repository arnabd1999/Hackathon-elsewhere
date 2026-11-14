import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import server


def _uni(i, name, industry="Fintech", verification="verified", quote="q", receipt="https://r"):
    return {"t": float(i), "ev": {"type": "universe", "id": f"u{i}", "name": name, "industry": industry,
                                  "one_liner": f"{name} does things", "evidence_quote": quote,
                                  "source_url": f"https://src/{i}", "receipt_url": receipt,
                                  "verification": verification, "kind": "company"}}


def _status(i, status):
    return {"t": float(i) + 0.5, "ev": {"type": "status", "id": f"u{i}", "status": status}}


class Showcase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.patch = mock.patch.object(server, "CACHE", self.dir)
        self.patch.start()
        server._showcase_cache.update(key=None, items=[])
        self.client = TestClient(server.app)

    def tearDown(self):
        self.patch.stop()
        server._showcase_cache.update(key=None, items=[])
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, fname, idea, events):
        (self.dir / fname).write_text(json.dumps({"idea": idea, "events": events}))

    def _get(self):
        r = self.client.get("/api/showcase")
        self.assertEqual(r.status_code, 200)
        return r.json()

    def test_empty_cache(self):
        self.assertEqual(self._get(), [])

    def test_verified_only_with_status_and_shape(self):
        self._write("a.json", "idea A", [
            _uni(1, "Alpha"), _status(1, "dead"),
            _uni(2, "Beta", verification="partial"),
            _uni(3, "Gamma", verification="unverified"),
            _uni(4, "Delta"),
        ])
        items = self._get()
        self.assertEqual([i["name"] for i in items], ["Alpha", "Delta"])
        self.assertEqual(items[0]["status"], "dead")
        self.assertEqual(items[1]["status"], "unknown")
        self.assertEqual(set(items[0]), {"name", "industry", "one_liner", "evidence_quote", "source_url",
                                         "receipt_url", "status", "idea"})
        self.assertEqual(items[0]["idea"], "idea A")

    def test_dedupe_by_lowercased_name(self):
        self._write("a.json", "A", [_uni(1, "Acme")])
        self._write("b.json", "B", [_uni(1, "ACME"), _uni(2, "Other")])
        names = [i["name"].lower() for i in self._get()]
        self.assertEqual(sorted(names), ["acme", "other"])

    def test_max_eight(self):
        self._write("a.json", "A", [_uni(i, f"Co{i}", industry=f"Ind{i % 3}") for i in range(20)])
        self.assertEqual(len(self._get()), 8)

    def test_industry_variety(self):
        evs = [_uni(i, f"Fin{i}", industry="Fintech") for i in range(10)]
        evs += [_uni(100 + i, f"Health{i}", industry="Health") for i in range(3)]
        evs += [_uni(200, "Edu0", industry="Education")]
        self._write("a.json", "A", evs)
        items = self._get()
        self.assertEqual(len(items), 8)
        inds = [i["industry"] for i in items]
        self.assertEqual(inds.count("Health"), 3)
        self.assertEqual(inds.count("Education"), 1)
        self.assertEqual(inds.count("Fintech"), 4)
        self.assertEqual(items, self._get())  # deterministic

    def test_prefers_items_with_evidence(self):
        evs = [_uni(i, f"Weak{i}", quote="", receipt="") for i in range(8)]
        evs += [_uni(50, "Strong")]
        self._write("a.json", "A", evs)
        self.assertEqual(self._get()[0]["name"], "Strong")

    def test_bad_json_ignored(self):
        (self.dir / "bad.json").write_text("{not json")
        self._write("good.json", "G", [_uni(1, "Fine")])
        self.assertEqual([i["name"] for i in self._get()], ["Fine"])

    def test_cache_refreshes_on_new_file(self):
        self._write("a.json", "A", [_uni(1, "One")])
        self.assertEqual(len(self._get()), 1)
        self._write("b.json", "B", [_uni(1, "Two")])
        self.assertEqual(len(self._get()), 2)


if __name__ == "__main__":
    unittest.main()

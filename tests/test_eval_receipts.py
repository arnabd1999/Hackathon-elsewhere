import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import eval_receipts  # noqa: E402


def universe(verification, name_on_page=None):
    ev = {"type": "universe", "id": "u", "name": "Acme", "verification": verification}
    if name_on_page is not None:
        ev["name_on_page"] = name_on_page
    return ev


def status(signal_url):
    return {"type": "status", "id": "u", "status": "active", "signal": "x", "signal_url": signal_url,
            "signal_date": None, "conflict": False}


class ScoreRunTests(unittest.TestCase):
    def test_counts_and_flags(self):
        events = [
            universe("verified", True),
            universe("verified", False),
            universe("partial", True),
            universe("unverified"),  # name_on_page missing -> not on page
            status("https://example.com/a"),
            status(None),
            {"type": "status", "id": "x", "status": "quiet", "signal_url": ""},
            {"type": "done"},
        ]
        got = eval_receipts.score_run(events)
        self.assertEqual(got, {
            "universes": 4,
            "verified": 2,
            "partial": 1,
            "unverified": 1,
            "name_on_page": 2,
            "with_status_receipt": 1,
        })

    def test_empty_events(self):
        self.assertEqual(eval_receipts.score_run([]), {
            "universes": 0, "verified": 0, "partial": 0, "unverified": 0,
            "name_on_page": 0, "with_status_receipt": 0,
        })


class CliTests(unittest.TestCase):
    def run_cli(self, directory):
        return subprocess.run(
            [sys.executable, "eval_receipts.py", str(directory)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60,
        )

    def test_empty_dir_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_cli(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("No recorded runs in cache/", proc.stdout)

    def test_scores_one_recorded_run(self):
        # server.py wraps each event as {"t": ..., "ev": {...}}; bare dicts must also work.
        wrapped = [
            {"t": 1.0, "ev": universe("verified", True)},
            {"t": 2.0, "ev": universe("unverified", False)},
            {"t": 3.0, "ev": status("https://example.com/a")},
            {"t": 4.0, "ev": {"type": "done"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "run1.json").write_text(json.dumps({"idea": "farm sms", "events": wrapped}))
            proc = self.run_cli(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("run1", proc.stdout)
        self.assertIn(
            "TOTAL 2 universes · 50% verified · 0% partial · 50% unverified · 50% name on page · 50% status with receipt",
            proc.stdout,
        )

    def test_zero_universes_prints_zero_percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "bare.json").write_text(json.dumps({"idea": "x", "events": [{"type": "error", "msg": "boom"}]}))
            proc = self.run_cli(tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            "TOTAL 0 universes · 0% verified · 0% partial · 0% unverified · 0% name on page · 0% status with receipt",
            proc.stdout,
        )


if __name__ == "__main__":
    unittest.main()

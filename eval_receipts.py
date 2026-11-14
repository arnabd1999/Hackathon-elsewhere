"""Receipts scorecard over recorded live runs in cache/*.json."""
import json
import sys
from pathlib import Path

KEYS = ("universes", "verified", "partial", "unverified", "name_on_page", "with_status_receipt")
DEFAULT_CACHE = Path(__file__).resolve().parent / "cache"


def score_run(events: list[dict]) -> dict:
    counts = dict.fromkeys(KEYS, 0)
    for ev in events:
        kind = ev.get("type")
        if kind == "universe":
            counts["universes"] += 1
            verification = ev.get("verification")
            if verification in ("verified", "partial", "unverified"):
                counts[verification] += 1
            if ev.get("name_on_page") is True:
                counts["name_on_page"] += 1
        elif kind == "status" and ev.get("signal_url"):
            counts["with_status_receipt"] += 1
    return counts


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def _line(c: dict) -> str:
    n = c["universes"]
    return (
        f"{n} universes · {_pct(c['verified'], n)}% verified · {_pct(c['partial'], n)}% partial · "
        f"{_pct(c['unverified'], n)}% unverified · {_pct(c['name_on_page'], n)}% name on page · "
        f"{_pct(c['with_status_receipt'], n)}% status with receipt"
    )


def _load_events(data: dict) -> list[dict]:
    # server.py stores each event wrapped as {"t": ..., "ev": {...}}; accept bare dicts too.
    return [item.get("ev", item) if isinstance(item, dict) else {} for item in data.get("events", [])]


def main(argv: list[str]) -> int:
    cache = Path(argv[1]) if len(argv) > 1 else DEFAULT_CACHE
    files = sorted(cache.glob("*.json"))
    if not files:
        print("No recorded runs in cache/")
        return 0
    total = dict.fromkeys(KEYS, 0)
    for path in files:
        try:
            data = json.loads(path.read_text())
            events = _load_events(data)
        except (OSError, ValueError, AttributeError) as e:
            print(f"{path.stem}: skipped ({e})", file=sys.stderr)
            continue
        counts = score_run(events)
        for k in KEYS:
            total[k] += counts[k]
        print(f"{path.stem}: {_line(counts)}")
    print(f"TOTAL {_line(total)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Receipts: check that a quote the LLM claims came from a page actually appears in that page."""
import re

_TRANS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-", " ": " "})


def _norm(s: str) -> str:
    s = s.translate(_TRANS)
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)  # markdown links/images -> text
    s = re.sub(r"[*_`#>|\\]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def verify_quote(quote: str, page_text: str) -> str:
    """Returns 'verified' (exact), 'partial' (most of it present) or 'unverified'."""
    q, p = _norm(quote or ""), _norm(page_text or "")
    if len(q) < 20 or not p:
        return "unverified"
    if q.strip(' ."\'') in p:
        return "verified"
    words = q.split()
    n = 6
    shingles = [" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))]
    hit = sum(1 for s in shingles if s in p) / len(shingles)
    return "partial" if hit >= 0.6 else "unverified"


if __name__ == "__main__":
    page = "## About\nWe help **small farmers** in Kenya sell produce directly to [restaurants](https://x.y) via SMS."
    assert verify_quote("We help small farmers in Kenya sell produce directly to restaurants via SMS.", page) == "verified"
    assert verify_quote("We help small farmers in Kenya sell produce directly to hotels using WhatsApp bots.", page) != "verified"
    assert verify_quote("Totally invented sentence about something else entirely here.", page) == "unverified"
    print("verify ok")

"""Receipts: check that a quote the LLM claims came from a page actually appears in that page."""
import html
import re
import unicodedata
import urllib.parse

_TRANS = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
                        "\u2013": "-", "\u2014": "-", "\u00a0": " "})
_ZW = re.compile("[\u200b\u200c\u200d\ufeff]")
_ELLIPSIS = re.compile("\u2026|\\.{3,}")


def _norm(s: str) -> str:
    s = html.unescape(s or "")
    s = _ZW.sub("", s)
    s = s.translate(_TRANS)
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)  # markdown links/images -> text
    s = re.sub(r"[*_`#>|\\]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def _fragments(quote: str) -> list[str]:
    return [f.strip() for f in _ELLIPSIS.split(quote or "") if f.strip()]


def _check_one(q: str, p: str) -> bool | float:
    """q, p normalized. Returns True (exact) or the shingle hit ratio."""
    if q.strip(' ."\'') in p:
        return True
    words = q.split()
    n = 6
    shingles = [" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1))]
    return sum(1 for s in shingles if s in p) / len(shingles)


def verify_quote(quote: str, page_text: str) -> str:
    """Returns 'verified' (exact), 'partial' (most of it present) or 'unverified'."""
    p = _norm(page_text)
    if not p:
        return "unverified"
    if _ELLIPSIS.search(quote or ""):
        frags = [f for f in (_norm(f) for f in _fragments(quote)) if len(f.split()) >= 4]
        if not frags:
            return "unverified"
        scores = []
        for f in frags:
            r = _check_one(f, p)
            scores.append(1.0 if r is True else 0.5 if r >= 0.6 else 0.0)
        if all(x == 1.0 for x in scores):
            return "verified"
        return "partial" if sum(scores) * 2 >= len(frags) else "unverified"
    q = _norm(quote)
    if len(q) < 20:
        return "unverified"
    r = _check_one(q, p)
    if r is True:
        return "verified"
    return "partial" if r >= 0.6 else "unverified"


def _fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _alnum(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", _fold(_norm(s)))).strip()


_SUFFIXES = {"inc", "llc", "ltd", "corp", "co", "gmbh", "plc"}


def _squash(s: str) -> str:
    return _alnum(s).replace(" ", "")


def name_on_page(name: str, page_text: str) -> bool:
    n, p = _alnum(name), _alnum(page_text)
    words = n.split()
    while len(words) > 1 and words[-1] in _SUFFIXES:
        words.pop()
    n = " ".join(words)
    if len(n) < 2 or not p:
        return False
    if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", p):
        return True
    sq = n.replace(" ", "")
    if len(sq) >= 4 and sq in p.replace(" ", ""):
        return True
    if 2 <= len(sq) <= 5 and sq.isalpha() and " " not in n:  # dotted acronym: I.B.M.
        return re.search(r"(?<!\w)" + r"\s".join(sq) + r"(?!\w)", p) is not None
    return False


def receipt_url(source_url: str, quote: str) -> str | None:
    """Source URL with a text-fragment that makes the browser highlight the quote."""
    if not source_url or len(_norm(quote)) < 20:
        return None
    clean = html.unescape(quote)
    clean = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", clean)
    clean = re.sub(r"[*_`]", "", clean)
    frags = _fragments(clean)
    words = (max(frags, key=lambda f: len(f.split())) if frags else clean).split()
    enc = lambda s: urllib.parse.quote(s, safe="").replace("-", "%2D")  # noqa: E731
    if len(words) <= 10:
        frag = enc(" ".join(words))
    else:
        frag = enc(" ".join(words[:5])) + "," + enc(" ".join(words[-5:]))
    return source_url.split("#", 1)[0] + "#:~:text=" + frag


def check_receipt(quote: str, page_text: str, company_name: str, source_url: str) -> dict:
    v = verify_quote(quote, page_text)
    on = name_on_page(company_name, page_text)
    if not on and v in ("verified", "partial"):
        v = "unverified"
    return {"verification": v, "name_on_page": on, "receipt_url": receipt_url(source_url, quote)}


if __name__ == "__main__":
    page = "## About\nWe help **small farmers** in Kenya sell produce directly to [restaurants](https://x.y) via SMS."
    assert verify_quote("We help small farmers in Kenya sell produce directly to restaurants via SMS.", page) == "verified"
    assert verify_quote("We help small farmers in Kenya sell produce directly to hotels using WhatsApp bots.", page) != "verified"
    assert verify_quote("Totally invented sentence about something else entirely here.", page) == "unverified"
    print("verify ok")

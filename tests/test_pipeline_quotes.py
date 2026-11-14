from pipeline import _build_universe, repair_quote

PAGE = """# About
We are [Too Good To Go](https://tgtg.example). Too Good To Go connects people with **surplus food** from local shops at a discount every day.
| col | col | col |
Our app is available in 19 countries and growing fast across Europe and North America.
"""
CORE = {"core_idea": "x", "user_execution": {}}


def _company(**kw):
    return {"name": "Too Good To Go", "one_liner": "surplus food app", "evidence_quote": "", **kw}


def test_repair_picks_the_sentence_naming_the_company():
    q = repair_quote(_company(evidence_quote="TGTG rescues surplus food from local shops"), PAGE)
    assert q == "Too Good To Go connects people with surplus food from local shops at a discount every day."


def test_repair_returns_none_when_company_not_on_page():
    assert repair_quote({"name": "Nobody Inc", "evidence_quote": "x", "one_liner": "y"}, PAGE) is None


def test_build_universe_repairs_invented_quote_and_marks_it():
    page = {"url": "https://tgtg.example/about", "markdown": PAGE}
    u = _build_universe(page, _company(evidence_quote="An invented sentence that never appears on this page at all."), CORE)
    assert u["verification"] == "verified"
    assert u["quote_repaired"] is True
    assert u["evidence_quote"].startswith("Too Good To Go connects people")


def test_build_universe_keeps_a_real_quote():
    real = "Too Good To Go connects people with surplus food from local shops at a discount every day."
    u = _build_universe({"url": "https://tgtg.example", "markdown": PAGE}, _company(evidence_quote=real), CORE)
    assert u["verification"] == "verified"
    assert u["quote_repaired"] is False
    assert u["evidence_quote"] == real


def test_company_missing_from_page_stays_unverified():
    page = {"url": "https://x.example", "markdown": PAGE}
    u = _build_universe(page, {"name": "Flashfood", "evidence_quote": "Flashfood sells groceries cheap.", "one_liner": "x"}, CORE)
    assert u["verification"] == "unverified"
    assert u["quote_repaired"] is False

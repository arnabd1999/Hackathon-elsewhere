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


def test_repair_skips_boilerplate_that_only_names_the_company():
    page = "Help others know if Too Good To Go is the product for them by leaving a review today."
    c = _company(evidence_quote="Too Good To Go sells surplus food from bakeries", one_liner="surplus food marketplace")
    assert repair_quote(c, page) is None


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


def test_off_page_company_is_credited_to_the_research_page_that_names_it():
    from pipeline import resource_page
    page = {"url": "https://blog.example/post", "markdown": PAGE, "lens": "cross", "lens_label": "Other industry"}
    sources = [
        {"url": "https://other.example/a", "title": "Unrelated", "snippets": ["Nothing here."]},
        {"url": "https://autoslash.example", "title": "AutoSlash",
         "snippets": ["AutoSlash tracks your rental car price and rebooks you automatically when it drops."]},
    ]
    c = {"name": "AutoSlash", "evidence_quote": "rebooks you when the price drops", "one_liner": "rental price tracker"}
    p = resource_page(page, c, sources)
    assert p["url"] == "https://autoslash.example" and p["lens"] == "cross"
    u = _build_universe(p, c, CORE)
    assert u["verification"] == "verified" and u["source_url"] == "https://autoslash.example"


def test_company_on_our_page_keeps_our_page():
    from pipeline import resource_page
    page = {"url": "https://tgtg.example", "markdown": PAGE}
    srcs = [{"url": "https://x.example", "title": "Too Good To Go", "snippets": ["Too Good To Go is great."]}]
    assert resource_page(page, {"name": "Too Good To Go"}, srcs) is page

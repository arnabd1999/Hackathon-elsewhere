"""Fields the frontend depends on: industry (clustered by exact string), geography (geocoded), transfer."""
from pipeline import _build_universe, clean_geography, title_industry, valid_name

PAGE = {"url": "https://x.example", "markdown": "Acme sells surplus bread from bakeries at a discount in Nairobi every evening."}
CORE = {"core_idea": "x", "user_execution": {}, "founder_industry": "food retail"}


def test_title_industry_keeps_acronyms():
    assert title_industry("food retail") == "Food Retail"
    assert title_industry("  last-mile   logistics ") == "Last-mile Logistics"
    assert title_industry("SaaS for services") == "SaaS For Services"
    assert title_industry("AI tutoring") == "AI Tutoring"


def test_geography_never_global_or_online():
    for g in ["global", "Online", "worldwide", "unspecified", "", None]:
        assert clean_geography(g) == "unknown"
    assert clean_geography("Nairobi, Kenya.") == "Nairobi, Kenya"


def test_valid_name_rejects_code_and_urls():
    assert not valid_name("console.text()")
    assert not valid_name("https://acme.com")
    assert not valid_name("{name}")
    assert valid_name("Kambr (Amadeus)")
    assert valid_name("Too Good To Go")
    assert valid_name("1-800-Flowers")


def test_parallel_uses_founder_industry_and_inspiration_gets_transfer():
    par = _build_universe(PAGE, {"name": "Acme", "kind": "parallel", "industry": "bakery tech",
                                 "execution": {"geography": "global"}}, CORE)
    assert par["industry"] == "Food Retail"
    assert par["execution"]["geography"] == "unknown"
    insp = _build_universe({**PAGE, "lens": "cross"}, {"name": "Acme", "kind": "parallel", "industry": "airlines",
                                                       "lesson": "Price drops as departure nears."}, CORE)
    assert insp["kind"] == "inspiration" and insp["industry"] == "Airlines"
    assert insp["transfer"] == "Price drops as departure nears."

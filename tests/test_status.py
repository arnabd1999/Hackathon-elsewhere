import asyncio
import unittest

import status

U = {"id": "abc", "name": "Acme Foods", "website": "https://www.acmefoods.com", "one_liner": "Sells food"}


def R(url, title="", desc="", age=None):
    return {"url": url, "title": title, "description": desc, "snippets": [], "page_age": age}


class Relevant(unittest.TestCase):
    def test_name_match(self):
        r = R("https://news.example/a", "Acme Foods raises seed")
        self.assertEqual(status.relevant([r], "Acme Foods", ""), [r])

    def test_domain_match(self):
        r = R("https://www.acmefoods.com/blog", "Our update")
        self.assertEqual(status.relevant([r], "Acme Foods", "https://acmefoods.com"), [r])

    def test_url_squash_when_no_website(self):
        r = R("https://hello-fresh.com/x", "Meals")
        self.assertEqual(status.relevant([r], "HelloFresh", ""), [r])

    def test_drops_other_company(self):
        r = R("https://news.example/b", "Zenith Groceries launches app", "A food delivery startup")
        self.assertEqual(status.relevant([r], "Acme Foods", "https://acmefoods.com"), [])


class CheckStatus(unittest.TestCase):
    def setUp(self):
        self._s, self._c = status.you.search, status.llm.complete_json
        self.addCleanup(self._restore)
        self.seen = {}

    def _restore(self):
        status.you.search, status.llm.complete_json = self._s, self._c

    def _run(self, results, llm_out):
        async def search(client, q, count=8, freshness=None):
            return results

        async def cj(client, system, user, max_tokens=2000, domains=None):
            self.seen["user"] = user
            self.seen["domains"] = domains
            return llm_out

        status.you.search, status.llm.complete_json = search, cj
        return asyncio.run(status.check_status(None, asyncio.Semaphore(1), U))

    def test_quiet_when_none_relevant(self):
        out = self._run([R("https://n.example/x", "Other Co news")], {"status": "thriving"})
        self.assertEqual(out["status"], "quiet")
        self.assertEqual(out["id"], "abc")
        self.assertEqual(out["type"], "status")
        self.assertNotIn("user", self.seen)

    def test_unlisted_url_unknown(self):
        res = [R("https://n.example/a", "Acme Foods raises", age="2026-01-01")]
        out = self._run(res, {"status": "thriving", "signal": "x", "signal_url": "https://made.up/z"})
        self.assertEqual(out["status"], "unknown")
        self.assertEqual(out["signal"], "")
        self.assertIsNone(out["signal_url"])

    def test_listed_url_ok(self):
        res = [R("https://n.example/a", "Acme Foods raises", age="2026-01-01")]
        out = self._run(res, {"status": "thriving", "signal": "Raised", "signal_url": "https://n.example/a"})
        self.assertEqual(out["status"], "thriving")
        self.assertEqual(out["signal_url"], "https://n.example/a")
        self.assertEqual(out["signal_date"], "2026-01-01")
        self.assertIn("conflict", out)

    def test_newest_first(self):
        res = [R("https://n.example/old", "Acme Foods old", age="2024-01-01"),
               R("https://n.example/none", "Acme Foods undated"),
               R("https://n.example/new", "Acme Foods new", age="2026-06-01")]
        self._run(res, {"status": "active", "signal_url": "https://n.example/new"})
        u = self.seen["user"]
        self.assertLess(u.index("/new"), u.index("/old"))
        self.assertLess(u.index("/old"), u.index("/none"))

    def test_research_kept_on_result_domains(self):
        res = [R("https://www.news.example/a", "Acme Foods raises", age="2026-01-01"),
               R("https://blog.other.example/b", "Acme Foods launches", age="2025-01-01"),
               R("https://news.example/c", "Acme Foods hires", age="2024-01-01")]
        self._run(res, {"status": "active", "signal_url": "https://news.example/c"})
        self.assertEqual(self.seen["domains"], ["news.example", "blog.other.example"])


if __name__ == "__main__":
    unittest.main()

import unittest

from verify import check_receipt, name_on_page, receipt_url, verify_quote

PAGE = "## About\nWe help **small farmers** in Kenya sell produce directly to [restaurants](https://x.y) via SMS."
Q = "We help small farmers in Kenya sell produce directly to restaurants via SMS."


class VerifyQuote(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(verify_quote(Q, PAGE), "verified")

    def test_changed_ending_not_verified(self):
        q = "We help small farmers in Kenya sell produce directly to hotels using WhatsApp bots."
        self.assertNotEqual(verify_quote(q, PAGE), "verified")

    def test_invented(self):
        self.assertEqual(verify_quote("Totally invented sentence about something else entirely here.", PAGE), "unverified")

    def test_html_entity(self):
        page = "Our network, AT&amp;T partners and carriers, delivers messages worldwide."
        self.assertEqual(verify_quote("Our network, AT&T partners and carriers, delivers messages worldwide.", page), "verified")

    def test_zero_width_and_nbsp(self):
        page = "We help small farm​ers in Kenya sell﻿ produce directly to restaurants via SMS."
        self.assertEqual(verify_quote(Q, page), "verified")

    def test_ellipsis_both_parts(self):
        page = "We help small farmers in Kenya. Lots of other text here. Sell produce directly to restaurants via SMS today."
        self.assertEqual(verify_quote("We help small farmers in Kenya … sell produce directly to restaurants via SMS", page), "verified")
        self.assertEqual(verify_quote("We help small farmers in Kenya ... sell produce directly to restaurants via SMS", page), "verified")

    def test_ellipsis_one_part(self):
        page = "We help small farmers in Kenya. Lots of other text here."
        self.assertEqual(verify_quote("We help small farmers in Kenya … sell produce directly to restaurants via SMS", page), "partial")

    def test_ellipsis_no_parts(self):
        self.assertEqual(verify_quote("Completely different words appear right here … and nothing else matches the page at all", PAGE), "unverified")


class EllipsisPartial(unittest.TestCase):
    def test_changed_word_partial(self):
        page = "We help small farmers in Kenya sell produce directly to restaurants via SMS every day."
        q = "We help small farmers in Kenya sell produce directly to restaurants via SMS every week \u2026"
        self.assertEqual(verify_quote(q, page), "partial")


class NameOnPage(unittest.TestCase):
    def test_case_and_punct(self):
        self.assertTrue(name_on_page("Acme Foods", "...ACME, foods inc..."))

    def test_spaces_removed(self):
        self.assertTrue(name_on_page("Acme Foods", "visit acmefoods.com today"))

    def test_absent(self):
        self.assertFalse(name_on_page("Zed", "nothing"))

    def test_tolerant(self):
        for n, p in [("Acme, Inc.", "We at Acme build"), ("HelloFresh", "Hello Fresh meals"),
                     ("Caf\u00e9 Nero", "cafe nero"), ("IBM", "I.B.M. said")]:
            self.assertTrue(name_on_page(n, p), n)

    def test_tiny_name_boundary(self):
        self.assertFalse(name_on_page("Zed", "Zeddy"))

    def test_short(self):
        self.assertFalse(name_on_page("A", "a a a"))


class CheckReceipt(unittest.TestCase):
    def test_downgrade_when_name_absent(self):
        r = check_receipt(Q, PAGE, "Zorblax", "https://x.y/p")
        self.assertEqual(r["verification"], "unverified")
        self.assertFalse(r["name_on_page"])

    def test_verified_with_name(self):
        r = check_receipt(Q, PAGE, "Kenya", "https://x.y/p")
        self.assertEqual(r["verification"], "verified")
        self.assertTrue(r["name_on_page"])
        self.assertTrue(r["receipt_url"].startswith("https://x.y/p#:~:text="))


class ReceiptUrl(unittest.TestCase):
    def test_none_cases(self):
        self.assertIsNone(receipt_url("", Q))
        self.assertIsNone(receipt_url(None, Q))
        self.assertIsNone(receipt_url("https://x.y", "too short"))

    def test_short_fragment_whole(self):
        u = receipt_url("https://x.y/p", "Farmers, sell & grow #1 crops now")
        self.assertEqual(u, "https://x.y/p#:~:text=Farmers%2C%20sell%20%26%20grow%20%231%20crops%20now")

    def test_long_start_end_and_fragment_replaced(self):
        q = "One, two-three four five six seven eight nine ten & eleven #twelve"
        u = receipt_url("https://x.y/p#old", q)
        self.assertEqual(u, "https://x.y/p#:~:text=One%2C%20two%2Dthree%20four%20five%20six,"
                            "nine%20ten%20%26%20eleven%20%23twelve")
        self.assertEqual(u.count("#"), 1)
        self.assertNotIn("old", u)

    def test_longest_fragment_and_clean(self):
        q = "Short bit here ok \u2026 We **help** [small farmers](http://a.b) sell produce"
        self.assertEqual(receipt_url("https://x.y", q),
                         "https://x.y#:~:text=We%20help%20small%20farmers%20sell%20produce")

    def test_dash_encoded(self):
        u = receipt_url("https://x.y/p", "Alpha-beta gamma delta epsilon zeta eta theta iota kappa lambda mu")
        self.assertIn("Alpha%2Dbeta", u)


if __name__ == "__main__":
    unittest.main()

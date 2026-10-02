"""
Size parsing, site search, product specifications and the tile calculator page.
"""
import json
import re

from django.test import SimpleTestCase

from apps.products.search import search_products
from apps.products.sizes import display_size, same_size, size_in_cm, sizes_in_query

from .base import ShopTestCase


class SizeParsingTests(SimpleTestCase):
    def test_clear_sizes(self):
        self.assertEqual(size_in_cm("60x60cm"), (60.0, 60.0))
        self.assertEqual(size_in_cm("60X60cm"), (60.0, 60.0))
        self.assertEqual(size_in_cm("1200X600mm"), (120.0, 60.0))
        self.assertEqual(size_in_cm("600 x 600"), (60.0, 60.0))   # big numbers: millimetres
        self.assertEqual(size_in_cm("2x2"), (61.0, 61.0))         # small numbers: feet
        self.assertEqual(size_in_cm("2 x 4 ft"), (61.0, 121.9))
        self.assertEqual(display_size("1200X600mm"), "120×60 cm")
        self.assertEqual(display_size("60x60cm"), "60×60 cm")

    def test_unclear_sizes(self):
        for text in ("4/2", "", None, "large", "60"):
            self.assertIsNone(size_in_cm(text), text)
            self.assertIsNone(display_size(text), text)

    def test_matching_and_queries(self):
        self.assertTrue(same_size((61.0, 61.0), (60.0, 60.0)))      # 2x2 ft ~ 60x60 cm
        self.assertTrue(same_size((60.0, 120.0), (120.0, 60.0)))    # orientation doesn't matter
        self.assertFalse(same_size((30.0, 30.0), (60.0, 60.0)))
        self.assertEqual(sizes_in_query("grey 60 x 60 floor"), [(60.0, 60.0)])
        self.assertEqual(sizes_in_query("60×120 tiles"), [(60.0, 120.0)])


class SearchTests(ShopTestCase):
    def names(self, query):
        results, exact = search_products(query)
        return [p.name for p in results], exact

    def test_size_searches(self):
        for query in ("60x60", "60 x 60", "60X60cm", "60×60", "2x2", "600x600mm"):
            names, exact = self.names(query)
            self.assertIn("Myglamm Grey", names, query)
            self.assertNotIn("ALTROZ GREY", names, query)
            self.assertTrue(exact, query)
        names, _ = self.names("600x1200")
        self.assertEqual(names, ["JUNGLE LUSH"])

    def test_word_searches(self):
        self.assertEqual(self.names("matte bathroom")[0], ["JUNGLE LUSH"])
        grey, exact = self.names("grey")
        self.assertTrue(exact)
        self.assertEqual(set(grey), {"Myglamm Grey", "ALTROZ GREY", "LUXE GREY"})
        self.assertEqual(self.names("grey porcelain")[0], ["Myglamm Grey"])

    def test_inactive_products_never_appear(self):
        self.assertEqual(self.names("discontinued")[0], [])

    def test_no_results_and_partial_matches(self):
        self.assertEqual(self.names("outdoor anti skid")[0], [])
        names, exact = self.names("grey marble")
        self.assertFalse(exact)
        self.assertIn("Myglamm Grey", names)

    def test_search_page(self):
        response = self.client.get("/search/?q=60x60")
        self.assertContains(response, "Myglamm Grey")
        self.assertContains(response, 'content="noindex,follow"')
        self.assertContains(response, 'data-event-on-load="search"')

    def test_search_page_empty_state_and_escaping(self):
        response = self.client.get("/search/?q=<script>alert(1)</script>")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "Nothing matched")
        self.assertContains(response, 'href="/inquiry/"')

    def test_long_queries_are_truncated(self):
        response = self.client.get("/search/?q=" + "grey " * 200)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.context["query"]), 100)

    def test_header_links_to_search(self):
        self.assertContains(self.client.get("/"), 'href="/search/"')


class ProductPageTests(ShopTestCase):
    def test_specifications_show_only_filled_fields(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertIn("<dt class=\"text-on-surface-variant font-medium\">Material</dt>", html)
        self.assertNotIn(">Finish</dt>", html)
        self.assertNotIn(">Brand</dt>", html)

        self.product.finish = "Glossy"
        self.product.brand = "Example Ceramics"
        self.product.save()
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertIn(">Finish</dt>", html)
        self.assertIn("Glossy", html)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        product = next(n for n in ld["@graph"] if n["@type"] == "Product")
        self.assertEqual(product["brand"], {"@type": "Brand", "name": "Example Ceramics"})

    def test_descriptive_alt_text_and_full_size_link(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertIn('alt="Myglamm Grey 60×60 cm porcelain floor tile"', html)
        self.assertIn('id="full-size-link"', html)

    def test_no_uncategorized_label(self):
        html = self.client.get(self.no_category.get_absolute_url()).content.decode()
        self.assertNotIn("UNCATEGORIZED", html.upper().replace("UNCATEGORIZED TILE", ""))

    def test_links_to_calculator(self):
        self.assertContains(self.client.get(self.product.get_absolute_url()), 'href="/tile-calculator/"')


class TileCalculatorTests(ShopTestCase):
    def test_page_answers_the_question(self):
        response = self.client.get("/tile-calculator/")
        self.assertContains(response, "How Many Tiles Do I Need?")
        self.assertContains(response, "33 tiles of 2 × 2 ft, or 35 tiles of 60 × 60 cm")
        html = response.content.decode()
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        faq = next(n for n in ld["@graph"] if n["@type"] == "FAQPage")
        self.assertEqual(len(faq["mainEntity"]), 5)
        for question in faq["mainEntity"]:
            self.assertIn(question["name"], html)  # every FAQ in the markup is visible

    def test_in_sitemap(self):
        self.assertIn("/tile-calculator/", self.client.get("/sitemap.xml").content.decode())

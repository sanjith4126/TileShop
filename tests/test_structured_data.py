"""
Structured data (JSON-LD), breadcrumbs and heading structure.
"""
import json
import re
from decimal import Decimal

from django.test import override_settings

from apps.core.models import BusinessInfo
from apps.products.models import Product

from .base import ShopTestCase

SITE = "https://suwasthick.example"
BAD_VALUES = (None, "", [], {}, "None", "null", "undefined")


def graph(html):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert len(blocks) == 1, f"expected one JSON-LD block, found {len(blocks)}"
    data = json.loads(blocks[0])
    assert data["@context"] == "https://schema.org"
    return data["@graph"]


def nodes_of(nodes, type_):
    return [n for n in nodes if n.get("@type") == type_ or (isinstance(n.get("@type"), list) and type_ in n["@type"])]


def walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)
    yield value


@override_settings(SITE_URL=SITE)
class StructuredDataTests(ShopTestCase):
    def public_urls(self):
        return ["/", "/products/", "/products/floor-tiles/", "/products/bathroom-tiles/", "/about/",
                "/inquiry/", "/room-visualizer/", self.product.get_absolute_url(),
                self.unclear_size.get_absolute_url(), self.no_category.get_absolute_url(),
                self.out_of_stock.get_absolute_url()]

    def test_every_page_has_clean_valid_json_ld(self):
        for url in self.public_urls():
            nodes = graph(self.client.get(url).content.decode())
            for value in walk(nodes):
                self.assertNotIn(value, BAD_VALUES, url)
            for node in nodes:
                self.assertNotIn(node.get("@type"), ("Review", "AggregateRating"), url)
            self.assertNotIn("aggregateRating", json.dumps(nodes), url)
            self.assertEqual(len(nodes_of(nodes, "WebSite")), 1, url)

    def test_organization_without_confirmed_details(self):
        nodes = graph(self.client.get("/").content.decode())
        org = nodes_of(nodes, "Organization")[0]
        self.assertEqual(org["@id"], f"{SITE}/#organization")
        self.assertEqual(org["name"], "Suwasthik Tiles")
        self.assertIn("Bhavani", org["description"])
        for unconfirmed in ("address", "telephone", "email", "openingHours"):
            self.assertNotIn(unconfirmed, org)

    def test_store_with_confirmed_details(self):
        info = BusinessInfo.get_solo()
        info.details_confirmed = True
        info.postal_code = "638301"
        info.opening_hours_spec = "Mo-Sa 09:00-19:00"
        info.save()
        store = nodes_of(graph(self.client.get("/").content.decode()), "Store")[0]
        self.assertEqual(store["telephone"], "+91 98765 43210")
        self.assertEqual(store["address"]["addressLocality"], "Bhavani")
        self.assertEqual(store["address"]["postalCode"], "638301")
        self.assertEqual(store["openingHours"], ["Mo-Sa 09:00-19:00"])

    def test_product_and_offer(self):
        nodes = graph(self.client.get(self.product.get_absolute_url()).content.decode())
        product = nodes_of(nodes, "Product")[0]
        self.assertEqual(product["name"], "Myglamm Grey")
        self.assertEqual(product["url"], f"{SITE}{self.product.get_absolute_url()}")
        self.assertTrue(product["image"][0].startswith(f"{SITE}/media/"))
        self.assertEqual(product["material"], "Porcelain")
        self.assertEqual(product["size"], "60×60 cm")
        self.assertEqual(product["category"], "Floor Tiles")
        self.assertNotIn("brand", product)
        self.assertNotIn("sku", product)
        offer = product["offers"]
        self.assertEqual(offer["price"], "520.00")
        self.assertEqual(offer["priceCurrency"], "INR")
        self.assertEqual(offer["availability"], "https://schema.org/InStock")
        self.assertEqual(offer["priceSpecification"]["referenceQuantity"]["unitCode"], "FTK")
        self.assertEqual(offer["seller"], {"@id": f"{SITE}/#organization"})

    def test_unclear_size_and_out_of_stock(self):
        unclear = nodes_of(graph(self.client.get(self.unclear_size.get_absolute_url()).content.decode()), "Product")[0]
        self.assertNotIn("size", unclear)
        oos = nodes_of(graph(self.client.get(self.out_of_stock.get_absolute_url()).content.decode()), "Product")[0]
        self.assertEqual(oos["offers"]["availability"], "https://schema.org/OutOfStock")
        self.assertNotIn("image", oos)  # no image uploaded -> no image property

    def test_breadcrumb_markup_matches_visible_trail(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        crumbs = nodes_of(graph(html), "BreadcrumbList")[0]["itemListElement"]
        self.assertEqual([c["name"] for c in crumbs], ["Home", "Products", "Floor Tiles", "Myglamm Grey"])
        self.assertEqual(crumbs[2]["item"], f"{SITE}/products/floor-tiles/")
        trail = html.split('aria-label="Breadcrumb"', 1)[1].split("</nav>", 1)[0]
        for name in ("Home", "Products", "Floor Tiles", "Myglamm Grey"):
            self.assertIn(name, trail)
        self.assertIn('href="/products/floor-tiles/"', trail)

    def test_category_item_list(self):
        nodes = graph(self.client.get("/products/floor-tiles/").content.decode())
        items = nodes_of(nodes, "ItemList")[0]["itemListElement"]
        urls = [i["url"] for i in items]
        self.assertIn(f"{SITE}{self.product.get_absolute_url()}", urls)
        self.assertNotIn(f"{SITE}{self.inactive.get_absolute_url()}", urls)
        self.assertEqual(len(nodes_of(nodes, "BreadcrumbList")), 1)

    def test_json_ld_cannot_be_broken_out_of(self):
        tricky = Product.objects.create(
            name='Evil </script><script>alert(1)</script> Tile', description="x",
            price=Decimal("10.00"), category=self.floor,
        )
        html = self.client.get(tricky.get_absolute_url()).content.decode()
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        self.assertNotIn("<", block)
        names = [n.get("name") for n in json.loads(block)["@graph"]]
        self.assertIn('Evil </script><script>alert(1)</script> Tile', names)


class HeadingTests(ShopTestCase):
    def test_one_h1_per_page(self):
        urls = ["/", "/products/", "/products/floor-tiles/", "/products/wall-tiles/", "/about/", "/inquiry/",
                "/room-visualizer/", self.product.get_absolute_url(), "/cart/", "/accounts/login/",
                "/accounts/register/"]
        for url in urls:
            html = self.client.get(url).content.decode()
            self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1, url)

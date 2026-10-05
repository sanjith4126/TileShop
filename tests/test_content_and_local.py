"""
Content system (guides, policy pages), GEO/local SEO statements and the
analytics event layer.
"""
import json
import re

from django.contrib.auth.models import User
from django.test import override_settings
from django.utils.html import escape

from apps.content.models import Guide, Page
from apps.core.models import BusinessInfo

from .base import ShopTestCase


def jsonld(html):
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))["@graph"]


class DraftContentTests(ShopTestCase):
    def test_drafts_exist_and_are_unpublished(self):
        self.assertEqual(
            set(Guide.objects.values_list("slug", flat=True)),
            {"ceramic-vs-porcelain-tiles", "choosing-floor-tile-size", "matt-vs-glossy-bathroom-tiles"},
        )
        self.assertEqual(
            set(Page.objects.values_list("slug", flat=True)),
            {"privacy-policy", "terms-of-sale", "delivery-policy", "returns-and-breakage", "warranty"},
        )
        self.assertFalse(Guide.objects.filter(is_published=True).exists())
        self.assertFalse(Page.objects.filter(is_published=True).exists())

    def test_policy_drafts_mark_owner_items_and_mention_the_visualizer(self):
        for page in Page.objects.all():
            self.assertIn("[OWNER TO CONFIRM", page.body, page.slug)
        self.assertIn("Gemini", Page.objects.get(slug="privacy-policy").body)

    def test_drafts_are_hidden_from_the_public(self):
        self.assertEqual(self.client.get("/guides/ceramic-vs-porcelain-tiles/").status_code, 404)
        self.assertEqual(self.client.get("/policies/privacy-policy/").status_code, 404)
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertNotIn("/guides/", sitemap)
        self.assertNotIn("/policies/", sitemap)
        home = self.client.get("/").content.decode()
        self.assertNotIn("/policies/", home)
        self.assertNotIn("Buying Guides", home)

    def test_staff_can_preview_drafts_without_indexing(self):
        User.objects.create_user("staff", password="pass-12345-word", is_staff=True)
        self.client.login(username="staff", password="pass-12345-word")
        response = self.client.get("/guides/choosing-floor-tile-size/")
        self.assertContains(response, "Draft preview")
        self.assertContains(response, 'content="noindex,nofollow"')

    def test_guide_list_is_noindex_while_empty(self):
        self.assertContains(self.client.get("/guides/"), 'content="noindex,follow"')


class PublishedContentTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        self.guide = Guide.objects.get(slug="ceramic-vs-porcelain-tiles")
        # The draft migration links guides to categories by slug; test categories are created later.
        self.guide.related_category = self.floor
        self.guide.is_published = True
        self.guide.save()
        self.page = Page.objects.get(slug="privacy-policy")
        self.page.is_published = True
        self.page.save()

    def test_published_guide(self):
        response = self.client.get(self.guide.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Guide.objects.get(pk=self.guide.pk).published_at)
        html = response.content.decode()
        self.assertIn("index,follow", html)
        nodes = jsonld(html)
        article = next(n for n in nodes if n["@type"] == "Article")
        self.assertEqual(article["headline"], self.guide.title)
        crumbs = next(n for n in nodes if n["@type"] == "BreadcrumbList")["itemListElement"]
        self.assertEqual([c["name"] for c in crumbs], ["Home", "Guides", self.guide.title])
        self.assertIn("Myglamm Grey", html)  # related floor tiles are suggested

    def test_published_content_in_sitemap_and_footer(self):
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(self.guide.get_absolute_url(), sitemap)
        self.assertIn("/guides/", sitemap)
        self.assertIn(self.page.get_absolute_url(), sitemap)
        home = self.client.get("/").content.decode()
        self.assertIn('href="/guides/"', home)
        self.assertIn('href="/policies/privacy-policy/"', home)
        self.assertContains(self.client.get("/guides/"), escape(self.guide.title))


class GeoAndLocalTests(ShopTestCase):
    def test_business_statement_on_every_page(self):
        for url in ("/", "/about/", "/products/", self.product.get_absolute_url()):
            self.assertContains(self.client.get(url), "is a tile and sanitaryware showroom in Bhavani, Erode district")

    def test_contradictions_are_gone(self):
        home = self.client.get("/").content.decode()
        about = self.client.get("/about/").content.decode()
        self.assertNotIn("natural materials", home.lower())
        self.assertNotIn("Natural Materials", about)
        self.assertNotIn("natural stone", about)
        self.assertNotIn("Exotic Marble", home)
        self.assertIn("Product Categories", about)

    def test_about_uses_business_info(self):
        about = self.client.get("/about/").content.decode()
        self.assertIn("Opp. Kalyana Mandabam, Bhavani, Erode Dt, Tamil Nadu", about)
        self.assertIn("Open Mon–Sat, 9 AM to 7 PM", about)

    def test_showroom_block_respects_confirmation(self):
        html = self.client.get("/inquiry/").content.decode()
        showroom = html.split('id="showroom"', 1)[1].split("</section>", 1)[0]
        self.assertIn("Opp. Kalyana Mandabam", showroom)
        self.assertNotIn("Call +91", showroom)
        self.assertNotIn("Open Mon", showroom)

        info = BusinessInfo.get_solo()
        info.details_confirmed = True
        info.maps_url = "https://maps.google.com/?q=Suwasthik"
        info.save()
        html = self.client.get("/inquiry/").content.decode()
        showroom = html.split('id="showroom"', 1)[1].split("</section>", 1)[0]
        self.assertIn('href="tel:+919876543210"', showroom)
        self.assertIn("Open Mon–Sat, 9 AM to 7 PM", showroom)
        self.assertIn("Get Directions", showroom)


class AnalyticsTests(ShopTestCase):
    def test_no_provider_without_configuration(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("googletagmanager", html)
        self.assertNotIn("plausible.io", html)
        self.assertIn("js/analytics.js", html)

    @override_settings(ANALYTICS_PROVIDER="ga4", ANALYTICS_ID="G-TEST123")
    def test_ga4_when_configured(self):
        html = self.client.get("/").content.decode()
        self.assertIn("googletagmanager.com/gtag/js?id=G-TEST123", html)

    @override_settings(ANALYTICS_PROVIDER="ga4", ANALYTICS_ID="")
    def test_provider_without_id_loads_nothing(self):
        self.assertNotIn("googletagmanager", self.client.get("/").content.decode())

    def test_events_are_declared(self):
        self.assertContains(self.client.get("/products/"), 'data-event="add_to_cart"')
        product = self.client.get(self.product.get_absolute_url())
        self.assertContains(product, 'data-event-on-load="product_view"')
        self.assertContains(self.client.get("/products/floor-tiles/"), 'data-event-on-load="category_view"')

    def test_purchase_event_has_no_personal_data(self):
        self.add_to_cart(self.product)
        self.client.post("/orders/checkout/", {
            "full_name": "Meera Iyer", "email": "meera@example.com", "phone": "+91 90000 11111",
            "shipping_address": "1 Lake Road, Bhavani", "payment_method": "cash",
        }, follow=True)
        from apps.orders.models import Order
        order = Order.objects.get()
        html = self.client.get(f"/orders/success/{order.pk}/").content.decode()
        params = re.search(r'data-event-on-load="purchase" data-event-params=\'([^\']*)\'', html).group(1)
        data = json.loads(params)
        self.assertEqual(data["transaction_id"], order.order_number)
        for personal in ("Meera", "meera@example.com", "90000", "Lake Road"):
            self.assertNotIn(personal, params)

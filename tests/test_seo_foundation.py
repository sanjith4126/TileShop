"""
Technical SEO foundation: robots.txt, sitemap, clean URLs with 301s, canonical
and robots tags, titles/descriptions, 404/500 pages, favicon, business info.
"""
import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.test import override_settings

from apps.core.models import BusinessInfo, Category

from .base import ShopTestCase

SITE = "https://suwasthick.example"


def meta_content(html, attr, value):
    match = re.search(rf'<meta {attr}="{re.escape(value)}" content="([^"]*)"', html)
    return match.group(1) if match else None


def canonical(html):
    match = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    return match.group(1) if match else None


def title(html):
    return re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()


@override_settings(SITE_URL=SITE)
class RobotsAndSitemapTests(ShopTestCase):
    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        body = response.content.decode()
        for line in ("User-agent: *", "Disallow: /cart/", "Disallow: /orders/",
                     "Disallow: /room-visualizer/generate/", f"Sitemap: {SITE}/sitemap.xml"):
            self.assertIn(line, body)
        self.assertNotIn("admin", body)

    def test_sitemap_lists_only_indexable_urls(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(f"<loc>{SITE}/</loc>", body)
        self.assertIn(f"<loc>{SITE}/products/floor-tiles/</loc>", body)
        self.assertIn(f"<loc>{SITE}/products/bathroom-tiles/</loc>", body)
        self.assertIn(f"<loc>{SITE}{self.product.get_absolute_url()}</loc>", body)
        self.assertIn("<lastmod>", body)
        self.assertNotIn("/products/wall-tiles/", body)  # no products yet
        self.assertNotIn(self.inactive.get_absolute_url(), body)
        locations = re.findall(r"<loc>([^<]*)</loc>", body)
        self.assertTrue(locations)
        for loc in locations:
            self.assertTrue(loc.startswith(SITE), loc)
            for private in ("/cart/", "/orders/", "/accounts/", "/search/", "?"):
                self.assertNotIn(private, loc)


class UrlTests(ShopTestCase):
    def test_product_url_has_id_and_slug(self):
        self.assertEqual(self.product.get_absolute_url(), f"/products/{self.product.pk}/myglamm-grey/")
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 200)

    def test_old_product_url_redirects_permanently(self):
        response = self.client.get(f"/products/{self.product.pk}/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], self.product.get_absolute_url())

    def test_wrong_slug_redirects_to_current_one(self):
        response = self.client.get(f"/products/{self.product.pk}/old-name/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], self.product.get_absolute_url())

    def test_inactive_and_unknown_products_are_404(self):
        self.assertEqual(self.client.get(self.inactive.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(f"/products/{self.inactive.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/products/999999/anything/").status_code, 404)

    def test_old_category_url_redirects_permanently(self):
        response = self.client.get(f"/products/?category={self.floor.pk}")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/products/floor-tiles/")
        response = self.client.get(f"/products/?category={self.floor.pk}&in_stock=1")
        self.assertEqual(response["Location"], "/products/floor-tiles/?in_stock=1")

    def test_bad_or_unknown_category_is_404(self):
        for value in ("abc", "999999", "-1"):
            self.assertEqual(self.client.get(f"/products/?category={value}").status_code, 404, value)
        self.assertEqual(self.client.get("/products/no-such-category/").status_code, 404)

    def test_category_page_includes_additional_categories(self):
        self.bath_product.additional_categories.add(self.floor)
        response = self.client.get("/products/floor-tiles/")
        self.assertContains(response, "JUNGLE LUSH")
        self.assertNotContains(response, "Discontinued Tile")

    def test_numeric_category_slug_is_rejected(self):
        with self.assertRaises(ValidationError):
            Category(name="Odd", slug="123").full_clean()

    def test_filters_combine_and_keep_category(self):
        response = self.client.get("/products/floor-tiles/?material=ceramic&in_stock=1")
        self.assertContains(response, "ALTROZ GREY")
        self.assertNotContains(response, "SCONE YELLOW")   # out of stock
        self.assertNotContains(response, "Myglamm Grey")  # porcelain
        self.assertContains(response, 'action="/products/floor-tiles/"')

    def test_invalid_filter_values_are_ignored(self):
        response = self.client.get("/products/?material=granite&in_stock=maybe")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Myglamm Grey")


@override_settings(SITE_URL=SITE)
class MetadataTests(ShopTestCase):
    def test_homepage(self):
        html = self.client.get("/").content.decode()
        self.assertEqual(title(html), "Suwasthick Tiles – Tiles &amp; Sanitaryware Showroom in Bhavani, Tamil Nadu")
        self.assertNotIn("Finest Tile Atelier", title(html))
        self.assertEqual(canonical(html), f"{SITE}/")
        self.assertTrue(meta_content(html, "name", "description"))
        self.assertTrue(meta_content(html, "name", "robots").startswith("index,follow"))
        self.assertTrue(meta_content(html, "property", "og:image").startswith(SITE))
        self.assertEqual(meta_content(html, "property", "og:locale"), "en_IN")

    def test_product_page(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertEqual(title(html), "Myglamm Grey – 60×60 cm Porcelain Floor Tile | Suwasthick Tiles")
        description = meta_content(html, "name", "description")
        self.assertIn("₹520", description)
        self.assertLessEqual(len(description), 160)
        self.assertEqual(canonical(html), f"{SITE}{self.product.get_absolute_url()}")
        self.assertEqual(meta_content(html, "property", "og:type"), "product")
        self.assertTrue(meta_content(html, "property", "og:image").startswith(f"{SITE}/media/"))

    def test_unclear_size_and_missing_category_are_handled(self):
        altroz = title(self.client.get(self.unclear_size.get_absolute_url()).content.decode())
        self.assertEqual(altroz, "ALTROZ GREY – Ceramic Floor Tile | Suwasthick Tiles")
        html = self.client.get(self.no_category.get_absolute_url()).content.decode()
        self.assertEqual(title(html), "LUXE GREY – Ceramic Tile | Suwasthick Tiles")
        head = html.split("</head>")[0]
        for bad in ("None", "Uncategorized", "4/2", "undefined"):
            self.assertNotIn(bad, head)

    def test_category_page(self):
        html = self.client.get("/products/floor-tiles/").content.decode()
        self.assertEqual(title(html), "Floor Tiles | Suwasthick Tiles, Bhavani")
        self.assertIn("3 floor tiles in ceramic and porcelain, including 60×60 cm, from ₹54 per sq. ft.", html)
        self.assertIn("Tiles designed for flooring applications", html)
        self.assertEqual(canonical(html), f"{SITE}/products/floor-tiles/")

    def test_filtered_listing_is_noindex_with_clean_canonical(self):
        html = self.client.get("/products/floor-tiles/?material=ceramic").content.decode()
        self.assertEqual(meta_content(html, "name", "robots"), "noindex,follow")
        self.assertEqual(canonical(html), f"{SITE}/products/floor-tiles/")

    def test_empty_category_is_helpful_and_noindex(self):
        html = self.client.get("/products/wall-tiles/").content.decode()
        self.assertEqual(meta_content(html, "name", "robots"), "noindex,follow")
        self.assertIn("We stock wall tiles at our Bhavani showroom", html)
        self.assertNotIn("tiles tiles", html.lower())
        self.assertIn('href="/inquiry/"', html)

    def test_tracking_parameters_are_not_in_canonical(self):
        html = self.client.get("/about/?utm_source=whatsapp&gclid=abc").content.decode()
        self.assertEqual(canonical(html), f"{SITE}/about/")

    def test_private_pages_are_noindex_without_canonical(self):
        for url in ("/cart/", "/accounts/login/", "/accounts/register/"):
            html = self.client.get(url).content.decode()
            self.assertTrue(meta_content(html, "name", "robots").startswith("noindex"), url)
            self.assertIsNone(canonical(html), url)

    def test_public_titles_and_descriptions_are_unique(self):
        urls = ["/", "/products/", "/products/floor-tiles/", "/products/bathroom-tiles/", "/about/",
                "/inquiry/", "/room-visualizer/", self.product.get_absolute_url(),
                self.unclear_size.get_absolute_url(), self.bath_product.get_absolute_url()]
        titles, descriptions = set(), set()
        for url in urls:
            html = self.client.get(url).content.decode()
            titles.add(title(html))
            descriptions.add(meta_content(html, "name", "description"))
        self.assertEqual(len(titles), len(urls))
        self.assertEqual(len(descriptions), len(urls))


class ErrorPageTests(ShopTestCase):
    def test_404_page(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "We couldn't find that page", status_code=404)
        self.assertContains(response, 'content="noindex,follow"', status_code=404)
        main = response.content.decode().split("<main", 1)[1].split("</main>", 1)[0]
        self.assertIn('href="/products/floor-tiles/"', main)
        self.assertNotIn('href="/products/wall-tiles/"', main)  # no products listed yet

    def test_500_page_needs_no_context(self):
        html = render_to_string("500.html")
        self.assertIn("Something went wrong", html)
        self.assertNotIn("{%", html)

    def test_favicon(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 302)
        self.assertIn("favicon", response["Location"])


class BusinessInfoTests(ShopTestCase):
    def test_unconfirmed_details_are_plain_text(self):
        html = self.client.get("/").content.decode()
        self.assertIn("+91 98765 43210", html)
        self.assertIn("studio@suwasthick.com", html)
        self.assertNotIn('href="tel:', html)
        self.assertNotIn('href="mailto:', html)

    def test_confirmed_details_become_clickable(self):
        info = BusinessInfo.get_solo()
        info.details_confirmed = True
        info.save()
        html = self.client.get("/").content.decode()
        self.assertIn('href="tel:+919876543210"', html)
        self.assertIn('href="mailto:studio@suwasthick.com"', html)

    def test_whatsapp_maps_and_social_links_appear_only_when_set(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("wa.me", html)
        self.assertNotIn("Get directions", html)
        info = BusinessInfo.get_solo()
        info.whatsapp = "91 98765 00000"
        info.maps_url = "https://maps.google.com/?q=Suwasthick+Tiles"
        info.instagram_url = "https://instagram.com/suwasthick"
        info.save()
        html = self.client.get("/").content.decode()
        self.assertIn('href="https://wa.me/919876500000"', html)
        self.assertIn("Get directions", html)
        self.assertIn('href="https://instagram.com/suwasthick"', html)

    def test_admin_opens_the_single_record(self):
        User.objects.create_superuser("boss", "boss@example.com", "pass-12345-word")
        self.client.login(username="boss", password="pass-12345-word")
        response = self.client.get("/admin/core/businessinfo/")
        self.assertRedirects(response, "/admin/core/businessinfo/1/change/")

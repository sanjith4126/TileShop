"""
Performance (image renditions, compiled CSS, icon subset, query counts) and
accessibility checks.
"""
import re
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.core.images import rendition_name, renditions_for
from apps.products.models import Product

from .base import ShopTestCase, image_upload

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


class RenditionTests(ShopTestCase):
    def test_renditions_created_on_upload_without_upscaling(self):
        big = Product.objects.create(name="Big Tile", description="x", price=Decimal("10"),
                                     category=self.floor, image=image_upload("big.png", size=(1500, 900)))
        widths = [w for w, _ in renditions_for(big.image.name, use_cache=False)]
        self.assertEqual(widths, [400, 800, 1200])
        small = Product.objects.create(name="Small Tile", description="x", price=Decimal("10"),
                                       category=self.floor, image=image_upload("small.png", size=(300, 200)))
        self.assertEqual([w for w, _ in renditions_for(small.image.name, use_cache=False)], [300])

    def test_replacing_and_deleting_an_image_removes_its_renditions(self):
        product = Product.objects.create(name="Swap Tile", description="x", price=Decimal("10"),
                                         category=self.floor, image=image_upload("swap.png", size=(900, 600)))
        old = product.image.name
        old_rendition = rendition_name(old, 400)
        self.assertTrue(default_storage.exists(old_rendition))
        product.name = "Swap Tile Two"  # new upload gets a new file name
        product.image = image_upload("swap-new.png", size=(900, 600))
        product.save()
        self.assertNotEqual(product.image.name, old)
        self.assertFalse(default_storage.exists(old_rendition))
        new_rendition = rendition_name(product.image.name, 400)
        self.assertTrue(default_storage.exists(new_rendition))
        product.delete()
        self.assertFalse(default_storage.exists(new_rendition))

    def test_pages_use_srcset(self):
        Product.objects.filter(pk=self.product.pk).update(is_featured=True)
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        main = re.search(r'<img [^>]*id="main-product-img"[^>]*>', html).group(0)
        self.assertIn('fetchpriority="high"', main)
        self.assertIn("srcset=", main)
        self.assertIn(".webp", main)
        self.assertNotIn('loading="lazy"', main)
        listing = self.client.get("/products/").content.decode()
        self.assertIn('loading="lazy"', listing)
        self.assertIn("-64w.webp 64w", listing)

    def test_first_listing_image_is_not_lazy(self):
        """On phones the first card's image is the largest element on screen (the LCP)."""
        for url in ("/products/", "/products/floor-tiles/", "/search/?q=grey"):
            html = self.client.get(url).content.decode()
            cards = re.findall(r'<article class="group[^>]*>.*?</article>', html, re.S)
            images = [re.search(r"<img [^>]*>", card).group(0) for card in cards if "<img " in card]
            self.assertGreater(len(images), 1, url)
            self.assertIn('fetchpriority="high"', images[0], url)
            self.assertNotIn('loading="lazy"', images[0], url)
            for img in images[1:]:
                self.assertIn('loading="lazy"', img, url)
                self.assertNotIn("fetchpriority", img, url)

    def test_build_command_and_unused_media_report(self):
        name = self.product.image.name
        for _, rendition in renditions_for(name, use_cache=False):
            default_storage.delete(rendition)
        out = StringIO()
        call_command("build_image_renditions", stdout=out)
        self.assertIn("Created", out.getvalue())
        self.assertTrue(renditions_for(name, use_cache=False))
        report = StringIO()
        call_command("find_unused_media", stdout=report)
        for _, rendition in renditions_for(name, use_cache=False):
            self.assertNotIn(rendition, report.getvalue())  # renditions of images in use are not 'unused'

    def test_stale_renditions_are_rebuilt(self):
        import os
        import time
        name = self.product.image.name
        rendition = renditions_for(name, use_cache=False)[0][1]
        old_time = time.time() - 3600
        os.utime(default_storage.path(rendition), (old_time, old_time))  # pretend it predates the original
        before = default_storage.get_modified_time(rendition)
        call_command("build_image_renditions", stdout=StringIO())
        self.assertGreater(default_storage.get_modified_time(rendition), before)


class FrontendAssetTests(ShopTestCase):
    def test_compiled_css_and_self_hosted_fonts(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("cdn.tailwindcss.com", html)
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertIn("/static/css/site.css", html)
        self.assertIn('rel="preload"', html)
        self.assertIn('as="font"', html)

    def test_every_font_file_exists(self):
        root = TEMPLATES.parent
        fonts_css = (root / "frontend" / "fonts.css").read_text(encoding="utf-8")
        files = re.findall(r'"\.\./fonts/([^"]+)"', fonts_css)
        self.assertTrue(files)
        for name in files:
            self.assertTrue((root / "static" / "fonts" / name).exists(), name)
        built = (root / "static" / "css" / "site.css").read_text(encoding="utf-8")
        self.assertEqual(built.count("@font-face"), len(files), "rebuild the CSS: npm run build:css")

    def test_every_icon_used_is_in_the_font_subset(self):
        fonts_css = (TEMPLATES.parent / "frontend" / "fonts.css").read_text(encoding="utf-8")
        subset = set(re.search(r"Material Symbols subset \(\d+ icons\): ([a-z0-9_,]+)", fonts_css).group(1).split(","))
        used = set()
        for path in TEMPLATES.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            used |= set(re.findall(r'data-icon="([a-z0-9_]+)"', text))
            used |= set(re.findall(r"dataset\.icon = [^;]*?'([a-z0-9_]+)'", text))
        self.assertFalse(used - subset, f"run scripts/update_fonts.py to add: {sorted(used - subset)}")

    def test_icon_names_are_not_page_text(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        self.assertNotRegex(html, r'material-symbols-outlined[^>]*>\s*[a-z_]+\s*<')
        for icon in re.findall(r'<span class="material-symbols-outlined[^"]*"[^>]*>', html):
            self.assertIn('aria-hidden="true"', icon)


class QueryCountTests(ShopTestCase):
    """Pages must not run one extra query per product (N+1)."""

    def count(self, url):
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(ctx.captured_queries)

    def test_query_counts_do_not_grow_with_products(self):
        urls = ["/", "/products/", "/products/floor-tiles/", self.product.get_absolute_url(), "/search/?q=grey"]
        self.client.get("/")  # warm the navigation cache
        before = {url: self.count(url) for url in urls}
        for i in range(8):
            Product.objects.create(name=f"Extra Grey {i}", description="grey", price=Decimal("50"),
                                   category=self.floor, is_featured=True)
        self.client.get("/")
        after = {url: self.count(url) for url in urls}
        for url in urls:
            self.assertLessEqual(after[url], before[url] + 1, f"{url}: {before[url]} -> {after[url]} queries")

    def test_cart_count_is_one_query(self):
        self.add_to_cart(self.product, 2)
        self.add_to_cart(self.bath_product, 1)
        with CaptureQueriesContext(connection) as ctx:
            self.client.get("/about/")
        cart_queries = [q for q in ctx.captured_queries if "cart_cartitem" in q["sql"]]
        self.assertEqual(len(cart_queries), 1)


class AccessibilityTests(ShopTestCase):
    def test_skip_link_and_content_target(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="#content"', html)
        self.assertIn('id="content"', html)

    def test_form_fields_have_labels(self):
        self.add_to_cart(self.product)
        for url in ("/inquiry/", "/orders/checkout/", self.product.get_absolute_url(), "/tile-calculator/"):
            html = self.client.get(url).content.decode()
            for match in re.finditer(r"<(?:input|select|textarea)\b[^>]*>", html):
                tag = match.group(0)
                if 'type="hidden"' in tag:
                    continue
                field_id = re.search(r'\bid="([^"]+)"', tag)
                before = html[: match.start()]
                wrapped = before.rfind("<label") > before.rfind("</label>")  # inside a <label>
                labelled = wrapped or 'aria-label="' in tag or (field_id and f'for="{field_id.group(1)}"' in html)
                self.assertTrue(labelled, f"{url}: unlabelled field {tag[:90]}")

    def test_images_have_alt_and_no_dead_links(self):
        for url in ("/", "/products/", self.product.get_absolute_url(), "/room-visualizer/", "/about/"):
            html = self.client.get(url).content.decode()
            for img in re.findall(r"<img\b[^>]*>", html):
                self.assertRegex(img, r'\balt="', f"{url}: {img[:80]}")
            self.assertNotIn('href="#"', html, url)

    def test_icon_only_controls_have_names(self):
        html = self.client.get("/").content.decode()
        for label in ("Search tiles", "Shopping cart", "Sign in", "Open menu", "Scroll to top"):
            self.assertIn(f'aria-label="{label}"', html)

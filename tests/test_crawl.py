"""
Crawl the public site with the test client, following every internal link, and
fail on broken ones: a page that doesn't end in a 200 response, or a static or
media file that doesn't exist.
"""
import re
from collections import deque
from html import unescape
from urllib.parse import unquote, urljoin, urlsplit

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage

from apps.content.models import Guide, Page

from .base import ShopTestCase

LINK_RE = re.compile(r'\b(?:href|src)="([^"]*)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]*)"')
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
NOT_LINKS = ("mailto:", "tel:", "javascript:", "data:", "#")
MAX_PAGES = 400


class CrawlTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        # Publish the drafts so their pages and links are crawled too.
        Guide.objects.update(is_published=True, related_category=self.floor)
        Page.objects.update(is_published=True, show_in_footer=True)

    def links_in(self, html, base):
        found = set(LINK_RE.findall(html))
        for srcset in SRCSET_RE.findall(html):
            found |= {candidate.strip().split(" ")[0] for candidate in srcset.split(",") if candidate.strip()}
        for raw in found:
            link = unescape(raw).strip()
            if not link or link.startswith(NOT_LINKS):
                continue
            parts = urlsplit(urljoin(base, link))
            if parts.scheme in ("http", "https") and parts.netloc not in ("testserver", ""):
                continue  # another website
            yield parts.path + (f"?{parts.query}" if parts.query else "")

    def check_file(self, path):
        """Static and media links must point at files that exist."""
        path = unquote(path.split("?")[0])
        if path.startswith(settings.STATIC_URL):
            return bool(finders.find(path[len(settings.STATIC_URL):]))
        return default_storage.exists(path[len(settings.MEDIA_URL):])

    def fetch(self, url):
        """Status after following redirects (at most 3 hops), and the final response."""
        response = self.client.get(url)
        hops = 0
        while response.status_code in (301, 302) and hops < 3:
            target = urlsplit(response["Location"])
            response = self.client.get(target.path + (f"?{target.query}" if target.query else ""))
            hops += 1
        return response

    def crawl(self):
        """Visit everything reachable from the homepage, the sitemap and the 404 page."""
        sitemap = self.client.get("/sitemap.xml").content.decode()
        start = ["/", "/robots.txt", "/this-page-does-not-exist/"]
        start += [urlsplit(loc).path for loc in LOC_RE.findall(sitemap)]

        queue = deque((url, "start") for url in start)
        seen = set(start)
        broken = []
        pages = files = 0
        while queue and pages < MAX_PAGES:
            url, source = queue.popleft()
            if url.startswith((settings.STATIC_URL, settings.MEDIA_URL)):
                files += 1
                if not self.check_file(url):
                    broken.append(f"{url} (missing file, linked from {source})")
                continue
            response = self.fetch(url)
            pages += 1
            expected = 404 if url == "/this-page-does-not-exist/" else 200
            if response.status_code != expected:
                broken.append(f"{url} -> {response.status_code} (linked from {source})")
                continue
            if "text/html" not in response.get("Content-Type", ""):
                continue
            for link in self.links_in(response.content.decode(), "http://testserver" + url):
                if link not in seen:
                    seen.add(link)
                    queue.append((link, url))
        self.assertLess(pages, MAX_PAGES, "crawl did not finish; is a link generating endless URLs?")
        return pages, files, broken, seen

    def test_no_broken_internal_links(self):
        pages, files, broken, seen = self.crawl()
        self.assertEqual(broken, [])
        self.assertGreater(pages, 30)
        self.assertGreater(files, 10)  # stylesheet, fonts, icons, product images and their renditions
        for page in ("/products/floor-tiles/", self.product.get_absolute_url(), "/guides/",
                     "/policies/privacy-policy/", "/tile-calculator/", "/search/", "/inquiry/"):
            self.assertIn(page, seen, f"{page} is not linked from anywhere")

    def test_the_crawler_notices_broken_links(self):
        Page.objects.filter(slug="warranty").update(
            body='<p><a href="/products/no-such-category/">Old link</a> <img src="/media/products/gone.jpg" alt=""></p>'
        )
        _, _, broken, _ = self.crawl()
        self.assertEqual(sorted(broken), [
            "/media/products/gone.jpg (missing file, linked from /policies/warranty/)",
            "/products/no-such-category/ -> 404 (linked from /policies/warranty/)",
        ])

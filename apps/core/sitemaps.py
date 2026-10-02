"""
XML sitemap: public pages, categories that have products, and active products.
Empty categories, filters, search, cart, checkout and accounts are left out.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.core.models import Category
from apps.products.models import Product
from apps.products.queries import category_last_modified, category_product_counts


class SiteUrlSitemap(Sitemap):
    """Use SITE_URL for absolute URLs when it is set, otherwise the request's host."""

    def get_protocol(self, protocol=None):
        if settings.SITE_URL:
            return urlsplit(settings.SITE_URL).scheme
        return super().get_protocol(protocol)

    def get_domain(self, site=None):
        if settings.SITE_URL:
            return urlsplit(settings.SITE_URL).netloc
        return super().get_domain(site)


class StaticPagesSitemap(SiteUrlSitemap):
    def items(self):
        return [
            "core:home",
            "products:product_list",
            "core:about",
            "core:inquiry",
            "core:room_visualizer",
            "core:tile_calculator",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(SiteUrlSitemap):
    def items(self):
        counts = category_product_counts()
        self._lastmod = category_last_modified()
        return [c for c in Category.objects.order_by("name") if counts.get(c.id)]

    def lastmod(self, category):
        return self._lastmod.get(category.id)


class ProductSitemap(SiteUrlSitemap):
    def items(self):
        return Product.objects.filter(is_active=True).order_by("pk")

    def lastmod(self, product):
        return product.updated_at


SITEMAPS = {
    "pages": StaticPagesSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}

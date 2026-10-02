"""
Site-wide template context: shop settings, navigation, business details and
SEO defaults shared by every page. Database-backed parts are cached and
refreshed whenever categories, products or business info change.
"""
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import DatabaseError

from .seo import INDEX, absolute_url, site_url
from .structured_data import organization_node, website_node

NAV_CACHE_KEY = "site:nav:v2"
BUSINESS_CACHE_KEY = "site:business:v1"
CACHE_SECONDS = 300

DEFAULT_TITLE = f"{settings.SITE_NAME} – Tiles & Sanitaryware Showroom in Bhavani, Tamil Nadu"
DEFAULT_DESCRIPTION = (
    "Tile and sanitaryware showroom in Bhavani, Erode district, Tamil Nadu. Floor, wall, bathroom, "
    "kitchen and parking tiles — order online and pay on delivery, or request a quote."
)
# Plain statement of who/what/where/how, shown in the footer of every page and
# used as the Organization description (product range confirmed by the owner).
BUSINESS_SUMMARY = (
    f"{settings.SITE_NAME} is a tile and sanitaryware showroom in Bhavani, Erode district, Tamil Nadu. "
    "It sells floor, wall, bathroom, kitchen and parking tiles and sanitaryware, takes orders online "
    "with payment on delivery, and gives quotes on request."
)


def _build_nav():
    """Categories (with product counts) and materials for menus, footer and 404 page."""
    from apps.core.models import Category
    from apps.products.models import Product
    from apps.products.queries import category_product_counts

    counts = category_product_counts()
    categories = [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "url": c.get_absolute_url(),
            "count": counts.get(c.id, 0),
            "image": c.image.name if c.image else "",
        }
        for c in Category.objects.order_by("name")
    ]
    labels = dict(Product.MATERIAL_CHOICES)
    materials = sorted(
        set(Product.objects.filter(is_active=True).order_by().values_list("material", flat=True))
    )
    fallback_image = next((c["image"] for c in categories if c["image"]), "")
    if not fallback_image:
        fallback_image = (
            Product.objects.filter(is_active=True).exclude(image="").exclude(image__isnull=True)
            .order_by("-is_featured", "-created_at").values_list("image", flat=True).first()
            or ""
        )
    return {
        "categories": categories,
        "materials": [{"value": m, "label": labels.get(m, m.title())} for m in materials if m],
        "fallback_image": fallback_image,
    }


def nav_data():
    return cache.get_or_set(NAV_CACHE_KEY, _build_nav, CACHE_SECONDS)


def get_business():
    """The BusinessInfo record (cached). Falls back to an empty record if the table is missing."""
    from apps.core.models import BusinessInfo

    business = cache.get(BUSINESS_CACHE_KEY)
    if business is None:
        try:
            business = BusinessInfo.get_solo()
        except DatabaseError:
            return BusinessInfo()
        cache.set(BUSINESS_CACHE_KEY, business, CACHE_SECONDS)
    return business


def clear_nav_cache(**kwargs):
    cache.delete(NAV_CACHE_KEY)


def clear_business_cache(**kwargs):
    cache.delete(BUSINESS_CACHE_KEY)
    cache.delete(NAV_CACHE_KEY)


def site(request):
    nav = nav_data()
    business = get_business()
    if business.share_image:
        share_image = business.share_image.url
    elif nav["fallback_image"]:
        share_image = default_storage.url(nav["fallback_image"])
    else:
        share_image = ""

    analytics_ok = settings.ANALYTICS_PROVIDER in ("ga4", "plausible") and settings.ANALYTICS_ID
    return {
        "site_name": settings.SITE_NAME,
        "site_url": site_url(request),
        "price_unit_label": settings.PRICE_UNIT_LABEL,
        "nav_categories": nav["categories"],
        "nav_materials": nav["materials"],
        "business": business,
        "default_title": DEFAULT_TITLE,
        "default_description": DEFAULT_DESCRIPTION,
        "default_robots": INDEX,
        "default_og_image": absolute_url(share_image, request) if share_image else "",
        "business_summary": BUSINESS_SUMMARY,
        "site_jsonld": [organization_node(request, business, BUSINESS_SUMMARY), website_node(request)],
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
        "bing_site_verification": settings.BING_SITE_VERIFICATION,
        "analytics_provider": settings.ANALYTICS_PROVIDER if analytics_ok else "",
        "analytics_id": settings.ANALYTICS_ID if analytics_ok else "",
    }

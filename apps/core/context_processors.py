"""
Site-wide template context: shop settings shared by every page.
"""
from django.conf import settings
from django.core.cache import cache

NAV_CACHE_KEY = "site:nav:v1"
NAV_CACHE_SECONDS = 300


def _build_nav():
    """Categories and product materials for the header/footer navigation."""
    from apps.core.models import Category
    from apps.products.models import Product

    labels = dict(Product.MATERIAL_CHOICES)
    materials = sorted(
        set(Product.objects.filter(is_active=True).order_by().values_list("material", flat=True))
    )
    return {
        "categories": list(Category.objects.order_by("name").values("id", "name", "slug")),
        "materials": [{"value": m, "label": labels.get(m, m.title())} for m in materials if m],
    }


def nav_data():
    return cache.get_or_set(NAV_CACHE_KEY, _build_nav, NAV_CACHE_SECONDS)


def clear_nav_cache(**kwargs):
    cache.delete(NAV_CACHE_KEY)


def site(request):
    nav = nav_data()
    return {
        "site_name": settings.SITE_NAME,
        "price_unit_label": settings.PRICE_UNIT_LABEL,
        "nav_categories": nav["categories"],
        "nav_materials": nav["materials"],
    }

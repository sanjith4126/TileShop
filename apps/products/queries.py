"""
Shared catalog queries.
"""
from collections import Counter

from django.db.models import Q

from .models import Product


def active_products():
    return Product.objects.filter(is_active=True).select_related("category")


def products_in_category(category):
    """Active products whose primary OR additional category is ``category``."""
    return (
        active_products()
        .filter(Q(category=category) | Q(additional_categories=category))
        .distinct()
    )


def _product_category_pairs():
    """{(product_id, category_id)} for active products, primary and additional categories."""
    pairs = set(
        Product.objects.filter(is_active=True, category__isnull=False).values_list("pk", "category_id")
    )
    through = Product.additional_categories.through
    pairs |= set(through.objects.filter(product__is_active=True).values_list("product_id", "category_id"))
    return pairs


def category_product_counts():
    """{category_id: number of active products} counting primary and additional categories once each."""
    return Counter(category_id for _, category_id in _product_category_pairs())


def category_last_modified():
    """{category_id: latest updated_at among its active products}."""
    updated = dict(Product.objects.filter(is_active=True).values_list("pk", "updated_at"))
    latest = {}
    for product_id, category_id in _product_category_pairs():
        stamp = updated.get(product_id)
        if stamp and (category_id not in latest or stamp > latest[category_id]):
            latest[category_id] = stamp
    return latest

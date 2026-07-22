"""
Products app views - product list and detail pages.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Product


def product_list(request):
    """Display all products with optional category filter."""
    from django.db.models import Q
    from apps.core.models import Category

    products = Product.objects.filter(is_active=True)
    category_id = request.GET.get("category", "")
    if category_id:
        # Match the primary category OR any additional category
        products = products.filter(
            Q(category_id=category_id) | Q(additional_categories__id=category_id)
        ).distinct()

    categories = Category.objects.all().order_by("name")

    context = {
        "products": products,
        "categories": categories,
        "selected_category": category_id,
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, pk):
    """Display a single product with its image gallery and related tiles."""
    from django.db.models import Q
    from apps.core.views import ROOM_TEMPLATES
    product = get_object_or_404(Product, pk=pk, is_active=True)

    # Related products share any category (primary or additional)
    cat_ids = [c.id for c in product.all_categories]
    related_products = []
    if cat_ids:
        related_products = (
            Product.objects.filter(is_active=True)
            .filter(Q(category_id__in=cat_ids) | Q(additional_categories__id__in=cat_ids))
            .exclude(pk=pk)
            .distinct()[:4]
        )

    context = {
        "product": product,
        "related_products": related_products,
        "gallery": product.gallery.all(),
        "rooms": ROOM_TEMPLATES,
    }
    return render(request, "products/product_detail.html", context)

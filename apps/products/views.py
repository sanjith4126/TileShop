"""
Products app views - product list and detail pages.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from apps.core.models import Category
from apps.core.utils import parse_positive_int

from .models import Product


def product_list(request):
    """Display all products with optional category filter."""
    products = Product.objects.filter(is_active=True).select_related("category")
    category_id = parse_positive_int(request.GET.get("category"))
    if category_id:
        # Match the primary category OR any additional category
        products = products.filter(
            Q(category_id=category_id) | Q(additional_categories__id=category_id)
        ).distinct()
    material = request.GET.get("material", "")
    if material in dict(Product.MATERIAL_CHOICES):
        products = products.filter(material=material)
    if request.GET.get("in_stock"):
        products = products.filter(stock__gt=0)

    categories = Category.objects.all().order_by("name")

    context = {
        "products": products,
        "categories": categories,
        "selected_category": str(category_id or ""),
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, pk):
    """Display a single product with its image gallery and related tiles."""
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk, is_active=True)

    # Related products share any category (primary or additional)
    cat_ids = [c.id for c in product.all_categories]
    related_products = []
    if cat_ids:
        related_products = (
            Product.objects.filter(is_active=True)
            .filter(Q(category_id__in=cat_ids) | Q(additional_categories__id__in=cat_ids))
            .exclude(pk=pk)
            .select_related("category")
            .distinct()[:4]
        )

    context = {
        "product": product,
        "related_products": related_products,
        "gallery": product.gallery.all(),
    }
    return render(request, "products/product_detail.html", context)

"""
Guides and policy pages. Drafts are visible only to staff (as a noindex preview).
"""
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.core.seo import INDEX, NOINDEX_FOLLOW, NOINDEX_NOFOLLOW, page_meta
from apps.core.structured_data import article_node, breadcrumb_node
from apps.products.queries import products_in_category

from .models import Guide, Page


def _visible(request, obj):
    """Published objects for everyone; drafts only for staff (preview)."""
    if obj.is_published:
        return False
    if request.user.is_authenticated and request.user.is_staff:
        return True
    raise Http404("Not published")


def guide_list(request):
    guides = list(Guide.objects.filter(is_published=True).select_related("related_category"))
    breadcrumbs = [{"name": "Home", "url": reverse("core:home")},
                   {"name": "Guides", "url": reverse("content:guide_list")}]
    context = {
        "guides": guides,
        "breadcrumbs": breadcrumbs,
        "jsonld": [breadcrumb_node(request, breadcrumbs)],
        "seo": page_meta(
            request,
            "Tile Buying Guides",
            "Practical advice on choosing tiles: materials, sizes and finishes for each room, from Suwasthick Tiles in Bhavani.",
            robots=INDEX if guides else NOINDEX_FOLLOW,
        ),
    }
    return render(request, "content/guide_list.html", context)


def guide_detail(request, slug):
    guide = get_object_or_404(Guide.objects.select_related("related_category"), slug=slug)
    preview = _visible(request, guide)
    breadcrumbs = [{"name": "Home", "url": reverse("core:home")},
                   {"name": "Guides", "url": reverse("content:guide_list")},
                   {"name": guide.title, "url": guide.get_absolute_url()}]
    related_products = []
    if guide.related_category:
        related_products = list(products_in_category(guide.related_category)[:4])
    context = {
        "guide": guide,
        "preview": preview,
        "related_products": related_products,
        "breadcrumbs": breadcrumbs,
        "jsonld": [breadcrumb_node(request, breadcrumbs), article_node(request, guide)],
        "seo": page_meta(
            request,
            guide.title,
            guide.summary,
            robots=NOINDEX_NOFOLLOW if preview else INDEX,
            og_type="article",
            image=guide.cover_image.url if guide.cover_image else "",
        ),
    }
    return render(request, "content/guide_detail.html", context)


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug)
    preview = _visible(request, page)
    context = {
        "page": page,
        "preview": preview,
        "seo": page_meta(
            request,
            page.title,
            page.meta_description or f"{page.title} for Suwasthick Tiles, Bhavani.",
            robots=NOINDEX_NOFOLLOW if preview else INDEX,
        ),
    }
    return render(request, "content/page_detail.html", context)

"""
Products app views — catalog listing, category landing pages and product pages.

URLs:
    /products/                      all products (filters: ?material=, ?in_stock=1)
    /products/<category-slug>/      category landing page (same filters)
    /products/<id>/<slug>/          product page
Old URLs (/products/?category=<id>, /products/<id>/) redirect permanently.
"""
import re

from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.cart.views import max_quantity
from apps.core.models import Category
from apps.core.seo import INDEX, NOINDEX_FOLLOW, first_sentence, page_meta
from apps.core.structured_data import breadcrumb_node, item_list_node, product_node
from apps.core.utils import parse_positive_int

from .models import Product
from .queries import active_products, category_product_counts, products_in_category
from .search import search_products
from .sizes import display_size


def format_price(value):
    """'54' for whole rupees, '54.50' otherwise."""
    return f"{value:,.0f}" if value == value.to_integral_value() else f"{value:,.2f}"


def _join_words(words):
    words = list(words)
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def _noun(category, count):
    if category is None:
        return "product" if count == 1 else "products"
    name = category.name.strip().lower()
    if name.endswith("tiles"):
        return name[:-1] if count == 1 else name
    return f"{name} product" if count == 1 else f"{name} products"


def listing_summary(products, category=None):
    """
    A factual sentence built from the data, e.g.
    "12 floor tiles in ceramic and porcelain, including 60×60 cm and 120×60 cm, from ₹54 per sq. ft."
    """
    # The primary key keeps products with the same material, size and price from
    # being merged by the DISTINCT that category querysets use.
    rows = [row[1:] for row in products.order_by().values_list("pk", "material", "size", "price")]
    if not rows:
        return ""
    labels = dict(Product.MATERIAL_CHOICES)
    materials = sorted({labels.get(m, m).lower() for m, _, _ in rows if m})
    sizes = []
    for _, size, _ in rows:
        shown = display_size(size)
        if shown and shown not in sizes:
            sizes.append(shown)
    text = f"{len(rows)} {_noun(category, len(rows))}"
    if materials:
        text += f" in {_join_words(materials)}"
    if sizes:
        text += f", including {_join_words(sizes[:3])}"
    lowest = min(price for _, _, price in rows)
    text += f", from ₹{format_price(lowest)} per {settings.PRICE_UNIT_LABEL}."
    return text


def mark_first_image(products):
    """Flag the first product that has a photo. On phones it is the largest thing on
    screen (the LCP element), so the card loads it eagerly instead of lazily."""
    for product in products:
        if product.image:
            product.eager_image = True
            break
    return products


def product_list(request):
    """All products. Old ?category=<id> links redirect to the category page."""
    if "category" in request.GET:
        return _legacy_category_redirect(request)
    return _listing(request)


def category_detail(request, category_slug):
    """Category landing page."""
    category = get_object_or_404(Category, slug=category_slug)
    return _listing(request, category)


def _legacy_category_redirect(request):
    params = request.GET.copy()
    raw = params.pop("category", [""])[-1]
    query = ("?" + params.urlencode()) if params else ""
    if not raw:
        return HttpResponsePermanentRedirect(reverse("products:product_list") + query)
    category_id = parse_positive_int(raw)
    category = Category.objects.filter(pk=category_id).first() if category_id else None
    if category is None:
        raise Http404("Unknown category")
    return HttpResponsePermanentRedirect(category.get_absolute_url() + query)


def _listing(request, category=None):
    base = products_in_category(category) if category else active_products()
    labels = dict(Product.MATERIAL_CHOICES)
    available = sorted(set(base.order_by().values_list("material", flat=True)) - {""})

    material = request.GET.get("material", "")
    if material not in available:
        material = ""
    in_stock = request.GET.get("in_stock") in ("1", "on", "true")

    products = base
    if material:
        products = products.filter(material=material)
    if in_stock:
        products = products.filter(stock__gt=0)
    is_filtered = bool(material or in_stock)
    products = mark_first_image(list(products))

    summary = listing_summary(base, category)
    total = base.count()
    clean_url = category.get_absolute_url() if category else reverse("products:product_list")

    if category:
        if total:
            intro = (category.description or "").strip()
            if intro and intro[-1] not in ".!?":
                intro += "."
            description = " ".join(filter(None, [
                summary, intro, "Order online and pay on delivery, or visit our Bhavani showroom.",
            ]))
        else:
            description = (
                f"Ask Suwasthik Tiles in Bhavani about our {category.name.lower()} range — "
                "visit the showroom or request a quote."
            )
        seo = page_meta(
            request,
            f"{category.name} | {settings.SITE_NAME}, Bhavani",
            description,
            full_title=True,
            image=category.image.url if category.image else "",
            # Empty categories and filtered views stay out of the index.
            robots=NOINDEX_FOLLOW if (is_filtered or not total) else INDEX,
            canonical=clean_url if is_filtered else None,
        )
    else:
        seo = page_meta(
            request,
            "Tile Collection – Buy Tiles Online",
            f"{summary} Order online with payment on delivery or request a quote from Suwasthik Tiles in Bhavani.",
            robots=NOINDEX_FOLLOW if is_filtered else INDEX,
            canonical=clean_url if is_filtered else None,
        )

    breadcrumbs = [{"name": "Home", "url": reverse("core:home")},
                   {"name": "Products", "url": reverse("products:product_list")}]
    if category:
        breadcrumbs.append({"name": category.name, "url": clean_url})
    jsonld = [breadcrumb_node(request, breadcrumbs)]
    if products:
        jsonld.append(item_list_node(request, products, category.name if category else "Tile Collection"))

    counts = category_product_counts()
    related_categories = [
        c for c in Category.objects.order_by("name")
        if counts.get(c.id) and (category is None or c.id != category.id)
    ]

    context = {
        "products": products,
        "category": category,
        "summary": summary,
        "total": total,
        "materials_available": [(m, labels.get(m, m.title())) for m in available],
        "selected_material": material,
        "in_stock": in_stock,
        "is_filtered": is_filtered,
        "clean_url": clean_url,
        "related_categories": related_categories,
        "breadcrumbs": breadcrumbs,
        "jsonld": jsonld,
        "seo": seo,
    }
    return render(request, "products/product_list.html", context)


def product_legacy_redirect(request, pk):
    """/products/<id>/ -> /products/<id>/<slug>/"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return HttpResponsePermanentRedirect(product.get_absolute_url())


def product_title(product):
    """'Myglamm Grey – 60×60 cm Porcelain Floor Tile' (unclear sizes are left out)."""
    kind = product.category.singular_name if product.category else "Tile"
    spec = " ".join(filter(None, [product.clear_size, product.get_material_display(), kind]))
    return f"{product.name} – {spec}"


def product_description(product):
    """Meta description from real data: what it is, price, and how to buy."""
    body = re.sub(rf"^\s*{re.escape(product.name)}\s*[–—:-]\s*", "", product.description or "", flags=re.IGNORECASE)
    body = first_sentence(body)
    if body:
        body = body[0].upper() + body[1:]
        if body[-1] not in ".!?":
            body += "."
    spec = " ".join(filter(None, [product.clear_size, product.get_material_display().lower(), product.kind]))
    lead = (
        f"{product.name} – {spec} at ₹{format_price(product.price)} per {settings.PRICE_UNIT_LABEL}, "
        f"from Suwasthik Tiles in Bhavani."
    )
    return " ".join(filter(None, [lead, body, "Order online and pay on delivery."]))


def product_detail(request, pk, slug):
    """Display a single product with its image gallery and related tiles."""
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk, is_active=True)
    if slug != product.slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())

    categories = product.all_categories
    cat_ids = [c.id for c in categories]
    related_products = []
    if cat_ids:
        related_products = (
            active_products()
            .filter(Q(category_id__in=cat_ids) | Q(additional_categories__id__in=cat_ids))
            .exclude(pk=pk)
            .distinct()[:4]
        )

    gallery = list(product.gallery.all())
    specs = [
        ("Finish", product.finish), ("Colour", product.color), ("Thickness", product.thickness),
        ("Where to use", product.application), ("Slip resistance", product.slip_resistance),
        ("Brand", product.brand), ("Product code", product.sku),
    ]
    breadcrumbs = [{"name": "Home", "url": reverse("core:home")},
                   {"name": "Products", "url": reverse("products:product_list")}]
    if product.category:
        breadcrumbs.append({"name": product.category.name, "url": product.category.get_absolute_url()})
    breadcrumbs.append({"name": product.name, "url": product.get_absolute_url()})

    context = {
        "product": product,
        "product_categories": categories,
        "related_products": related_products,
        "gallery": gallery,
        "product_specs": [(label, value) for label, value in specs if value],
        "max_quantity": max_quantity(product),
        "breadcrumbs": breadcrumbs,
        "jsonld": [breadcrumb_node(request, breadcrumbs), product_node(request, product, categories, gallery)],
        "seo": page_meta(
            request,
            product_title(product),
            product_description(product),
            og_type="product",
            image=product.image.url if product.image else "",
        ),
    }
    return render(request, "products/product_detail.html", context)


def search(request):
    """Site search: /search/?q=. Results are never indexed."""
    query = " ".join(request.GET.get("q", "").split())[:100]
    results, exact = search_products(query) if query else ([], True)
    mark_first_image(results)
    title = f"Search results for “{query}”" if query else "Search Tiles"
    context = {
        "query": query,
        "results": results,
        "exact": exact,
        "seo": page_meta(
            request,
            title,
            "Search the Suwasthik Tiles collection by name, size, material or room.",
            robots=NOINDEX_FOLLOW,
        ),
    }
    return render(request, "search.html", context)

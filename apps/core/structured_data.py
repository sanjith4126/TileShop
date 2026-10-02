"""
Schema.org JSON-LD builders.

Rules: only real data, nothing that isn't visible on the page, no empty values.
Business contact details (address, phone, hours...) are only published once
the owner ticks "details confirmed" in the admin. No Review/AggregateRating:
the site has no genuine review data.
"""
from django.conf import settings

from .seo import absolute_url, clean_text, site_url


def clean(value):
    """Drop None, empty strings, empty lists and empty dicts, recursively."""
    if isinstance(value, dict):
        cleaned = {k: clean(v) for k, v in value.items()}
        return {k: v for k, v in cleaned.items() if v not in (None, "", [], {})}
    if isinstance(value, (list, tuple)):
        cleaned = [clean(v) for v in value]
        return [v for v in cleaned if v not in (None, "", [], {})]
    return value


def organization_id(request):
    return f"{site_url(request)}/#organization"


def organization_node(request, business, description):
    base = site_url(request)
    node = {
        "@type": "Store" if business.details_confirmed else "Organization",
        "@id": organization_id(request),
        "name": settings.SITE_NAME,
        "url": f"{base}/",
        "description": description,
        "logo": absolute_url(business.logo.url, request) if business.logo else None,
        "image": absolute_url(business.share_image.url, request) if business.share_image else None,
        "sameAs": [url for _, url in business.social_links],
    }
    if business.details_confirmed:
        node.update({
            "address": {
                "@type": "PostalAddress",
                "streetAddress": business.street_address,
                "addressLocality": business.locality,
                "addressRegion": business.region,
                "postalCode": business.postal_code,
                "addressCountry": business.country,
            },
            "telephone": business.phone,
            "email": business.email,
            "openingHours": [s.strip() for s in business.opening_hours_spec.split(",") if s.strip()],
            "hasMap": business.maps_url,
            "areaServed": [a.strip() for a in business.service_areas.split(",") if a.strip()],
        })
        if business.latitude is not None and business.longitude is not None:
            node["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": float(business.latitude),
                "longitude": float(business.longitude),
            }
    return clean(node)


def website_node(request):
    base = site_url(request)
    return {
        "@type": "WebSite",
        "@id": f"{base}/#website",
        "url": f"{base}/",
        "name": settings.SITE_NAME,
        "inLanguage": "en-IN",
        "publisher": {"@id": organization_id(request)},
    }


def breadcrumb_node(request, breadcrumbs):
    """``breadcrumbs`` is the same list the visible breadcrumb trail renders: [{"name", "url"}, ...]."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": crumb["name"],
                "item": absolute_url(crumb["url"], request),
            }
            for position, crumb in enumerate(breadcrumbs, start=1)
        ],
    }


def item_list_node(request, products, name):
    return {
        "@type": "ItemList",
        "name": name,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "url": absolute_url(product.get_absolute_url(), request),
                "name": product.name,
            }
            for position, product in enumerate(products, start=1)
        ],
    }


def product_node(request, product, categories, gallery=()):
    url = absolute_url(product.get_absolute_url(), request)
    images = []
    if product.image:
        images.append(absolute_url(product.image.url, request))
    images += [absolute_url(item.image.url, request) for item in gallery if item.image]
    price = f"{product.price:.2f}"
    node = {
        "@type": "Product",
        "@id": f"{url}#product",
        "name": product.name,
        "description": clean_text(product.description),
        "url": url,
        "image": images,
        "category": categories[0].name if categories else None,
        "material": product.get_material_display(),
        "size": product.clear_size,  # None when the size is unclear (e.g. "4/2")
        "sku": getattr(product, "sku", ""),
        "color": getattr(product, "color", ""),
        "brand": {"@type": "Brand", "name": product.brand} if getattr(product, "brand", "") else None,
        "offers": {
            "@type": "Offer",
            "url": url,
            "price": price,
            "priceCurrency": settings.PRICE_CURRENCY,
            # The page shows "₹X / sq. ft": the price is for one square foot.
            "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": price,
                "priceCurrency": settings.PRICE_CURRENCY,
                "referenceQuantity": {
                    "@type": "QuantitativeValue",
                    "value": "1",
                    "unitCode": settings.PRICE_UNIT_CODE,
                    "unitText": settings.PRICE_UNIT_LABEL,
                },
            },
            "availability": "https://schema.org/InStock" if product.stock > 0 else "https://schema.org/OutOfStock",
            "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@id": organization_id(request)},
        },
    }
    return clean(node)


def article_node(request, guide, breadcrumbs=None):
    url = absolute_url(guide.get_absolute_url(), request)
    node = {
        "@type": "Article",
        "@id": f"{url}#article",
        "headline": guide.title,
        "description": clean_text(guide.summary),
        "url": url,
        "mainEntityOfPage": url,
        "image": absolute_url(guide.cover_image.url, request) if guide.cover_image else None,
        "datePublished": guide.published_at.isoformat() if guide.published_at else None,
        "dateModified": guide.updated_at.isoformat() if guide.updated_at else None,
        "author": {"@type": "Person", "name": guide.author_name} if guide.author_name else {"@id": organization_id(request)},
        "publisher": {"@id": organization_id(request)},
        "inLanguage": "en-IN",
    }
    return clean(node)


def faq_node(faqs):
    """``faqs``: [(question, answer_text), ...] — only questions shown on the page."""
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": clean_text(answer)},
            }
            for question, answer in faqs
        ],
    }

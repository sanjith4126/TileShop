"""
Template tags for SEO output.

    {% load seo_tags %}
    {% json_ld %}   -> one <script type="application/ld+json"> with the site-wide
                       nodes (Organization, WebSite) plus the page's own `jsonld` nodes.
"""
import json

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

_ESCAPES = {ord("<"): "\\u003c", ord(">"): "\\u003e", ord("&"): "\\u0026"}


def dumps_for_html(data):
    """JSON that is safe inside a <script> element (no '</script>' breakouts)."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).translate(_ESCAPES)


@register.simple_tag(takes_context=True)
def json_ld(context):
    nodes = list(context.get("site_jsonld") or []) + list(context.get("jsonld") or [])
    if not nodes:
        return ""
    graph = {"@context": "https://schema.org", "@graph": nodes}
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(dumps_for_html(graph)))

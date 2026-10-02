"""
    {% load image_tags %}
    {% responsive_img product.image alt=product.descriptive_name sizes="(min-width: 1024px) 25vw, 50vw" css="w-full h-full object-cover" %}

Renders an <img> with a WebP srcset when renditions exist, falling back to the
original file. Images load lazily unless loading="eager" is passed; pass
fetchpriority="high" for the main image of a page.
"""
from django import template
from django.core.files.storage import default_storage
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from apps.core.images import renditions_for

register = template.Library()


@register.simple_tag
def rendition_srcset(image):
    """The srcset string for an image ('' if it has no renditions)."""
    if not image or not getattr(image, "name", ""):
        return ""
    return ", ".join(f"{default_storage.url(n)} {w}w" for w, n in renditions_for(image.name))


@register.simple_tag
def rendition_src(image):
    """A sensible single URL: the largest rendition up to 800px, else the original."""
    if not image or not getattr(image, "name", ""):
        return ""
    small = [n for w, n in renditions_for(image.name) if w <= 800]
    return default_storage.url(small[-1]) if small else image.url


@register.simple_tag
def responsive_img(image, alt="", sizes="100vw", css="", loading="lazy", fetchpriority="", img_id=""):
    if not image or not getattr(image, "name", ""):
        return ""
    renditions = renditions_for(image.name)
    attrs = [("alt", alt), ("class", css)]
    if renditions:
        # Default src: the largest rendition up to 800px wide.
        fallback = [n for w, n in renditions if w <= 800] or [renditions[0][1]]
        attrs.insert(0, ("src", default_storage.url(fallback[-1])))
        attrs.append(("srcset", ", ".join(f"{default_storage.url(n)} {w}w" for w, n in renditions)))
        attrs.append(("sizes", sizes))
    else:
        attrs.insert(0, ("src", image.url))
    if loading:
        attrs.append(("loading", loading))
    attrs.append(("decoding", "async"))
    if fetchpriority:
        attrs.append(("fetchpriority", fetchpriority))
    if img_id:
        attrs.append(("id", img_id))
    rendered = format_html_join(" ", '{}="{}"', ((k, v) for k, v in attrs if v or k == "alt"))
    return format_html("<img {}/>", mark_safe(rendered))

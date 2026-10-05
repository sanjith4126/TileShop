"""
SEO helpers: absolute URLs, page metadata (title, description, robots,
canonical, Open Graph) and description text utilities.

Every view passes ``seo=page_meta(...)`` to its template; ``base.html`` renders it.
"""
import re

from django.conf import settings
from django.utils.html import strip_tags

INDEX = "index,follow,max-image-preview:large"
NOINDEX_FOLLOW = "noindex,follow"
NOINDEX_NOFOLLOW = "noindex,nofollow"


def site_url(request=None):
    """Base URL without a trailing slash, e.g. "https://example.pythonanywhere.com"."""
    if settings.SITE_URL:
        return settings.SITE_URL
    if request is not None:
        return f"{request.scheme}://{request.get_host()}"
    return ""


def absolute_url(path_or_url, request=None):
    """Make a path absolute using SITE_URL (or the request host if SITE_URL isn't set)."""
    if not path_or_url:
        return ""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    if path_or_url.startswith("//"):
        return "https:" + path_or_url
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return site_url(request) + path_or_url


def clean_text(text):
    """Plain text with HTML removed and whitespace collapsed."""
    return " ".join(strip_tags(str(text or "")).split())


def truncate(text, limit=158):
    """Shorten text at a word boundary, adding an ellipsis when cut."""
    text = clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:–—-")
    return cut + "…"


def first_sentence(text):
    text = clean_text(text)
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    return match.group(1) if match else text


def page_meta(request, title, description="", *, robots=INDEX, canonical=None,
              og_type="website", image="", full_title=False):
    """
    Metadata for one page.

    - ``title`` gets " | Suwasthik Tiles" appended unless ``full_title`` is True.
    - Indexable pages get a canonical URL (this path, no query string) unless
      one is given; non-indexable pages only get one if it is passed explicitly.
    """
    indexable = not robots.startswith("noindex")
    if canonical is None and indexable:
        canonical = absolute_url(request.path, request)
    elif canonical:
        canonical = absolute_url(canonical, request)
    return {
        "title": title if full_title else f"{title} | {settings.SITE_NAME}",
        "description": truncate(description) if description else "",
        "robots": robots,
        "canonical": canonical or "",
        "og_type": og_type,
        "image": absolute_url(image, request) if image else "",
    }

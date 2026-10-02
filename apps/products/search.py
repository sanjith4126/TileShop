"""
Simple product search for a small catalog: plain database query, matching in
Python. Understands sizes the way buyers type them ("2x2", "60x60",
"600 x 1200 mm", "60×120"), and simple word variants ("matte" -> "matt").
"""
import re

from .queries import active_products
from .sizes import SIZE_IN_TEXT_RE, same_size, size_in_cm, sizes_in_query

MAX_QUERY_LENGTH = 100
STOPWORDS = {"tile", "tiles", "a", "an", "and", "for", "in", "of", "the", "with", "to", "my"}


def _variants(term):
    """'tiles' -> {'tiles', 'tile'}; 'matte' -> {'matte', 'matt'}."""
    variants = {term}
    if len(term) > 3:
        if term.endswith("es"):
            variants.add(term[:-2])
        if term.endswith("s"):
            variants.add(term[:-1])
        if term.endswith("e"):
            variants.add(term[:-1])
    return variants


def _haystack(product):
    parts = [
        product.name,
        product.description,
        product.get_material_display(),
        product.size,
        product.category.name if product.category else "",
        product.finish,
        product.color,
        product.brand,
        product.sku,
        product.application,
    ]
    parts += [c.name for c in product.additional_categories.all()]
    return " ".join(p for p in parts if p).lower().replace("×", "x")


def parse_query(query):
    """Split a query into (word terms, sizes in cm)."""
    query = (query or "").strip()[:MAX_QUERY_LENGTH]
    sizes = sizes_in_query(query)
    words_only = SIZE_IN_TEXT_RE.sub(" ", query.lower().replace("×", "x"))
    terms = [
        t for t in re.findall(r"[a-z0-9][a-z0-9-]*", words_only)
        # Lone digits ("1") would match inside every size and code, so they're ignored.
        if t not in STOPWORDS and not (t.isdigit() and len(t) < 2)
    ]
    return terms, sizes


def search_products(query):
    """
    Returns (products, exact). ``exact`` is False when nothing matched every
    term, in which case the closest partial matches are returned instead.
    """
    terms, sizes = parse_query(query)
    if not terms and not sizes:
        return [], True

    scored = []
    for product in active_products().prefetch_related("additional_categories"):
        haystack = _haystack(product)
        name = product.name.lower()
        matched, score = 0, 0
        for term in terms:
            variants = _variants(term)
            if any(v in haystack for v in variants):
                matched += 1
                score += 3 if any(v in name for v in variants) else 1
        size_ok = None
        if sizes:
            product_size = size_in_cm(product.size)
            size_ok = bool(product_size) and any(same_size(s, product_size) for s in sizes)
            if size_ok:
                score += 3
        wanted = len(terms) + (1 if sizes else 0)
        got = matched + (1 if size_ok else 0)
        if got:
            scored.append((got == wanted, score, product))

    exact = [p for full, s, p in sorted(scored, key=lambda x: -x[1]) if full]
    if exact:
        return exact, True
    partial = [p for _, s, p in sorted(scored, key=lambda x: -x[1])]
    return partial, False

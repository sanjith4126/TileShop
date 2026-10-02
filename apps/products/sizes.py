"""
Tile size parsing. Sizes are typed freely in the admin ("60x60cm",
"1200X600mm", "2x2 ft", "4/2"), so everything that shows or searches sizes
goes through here. Sizes that can't be read with confidence (like "4/2") are
treated as unclear and left out of titles, schema and summaries.
"""
import re

SIZE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*[x×X*]\s*(\d+(?:\.\d+)?)\s*"
    r"(mm|cm|ft|feet|foot|in|inch|inches|\"|')?\s*$",
    re.IGNORECASE,
)
SIZE_IN_TEXT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[x×X*]\s*(\d+(?:\.\d+)?)\s*(mm|cm|ft|feet|foot|in|inch|inches)?",
    re.IGNORECASE,
)
_TO_CM = {
    "mm": 0.1, "cm": 1.0,
    "ft": 30.48, "feet": 30.48, "foot": 30.48, "'": 30.48,
    "in": 2.54, "inch": 2.54, "inches": 2.54, '"': 2.54,
}


def _to_cm(a, b, unit):
    unit = (unit or "").lower()
    if not unit:
        biggest = max(a, b)
        # "600x600" is millimetres, "2x2" is feet, "60x60" is centimetres.
        unit = "mm" if biggest >= 200 else ("ft" if biggest <= 10 else "cm")
    factor = _TO_CM[unit]
    return round(a * factor, 1), round(b * factor, 1)


def size_in_cm(text):
    """(width_cm, height_cm) for a clearly written size, otherwise None."""
    match = SIZE_RE.match(str(text or ""))
    if not match:
        return None
    return _to_cm(float(match.group(1)), float(match.group(2)), match.group(3))


def sizes_in_query(text):
    """Every size mentioned in a search query, as (cm, cm) pairs."""
    return [
        _to_cm(float(a), float(b), unit)
        for a, b, unit in SIZE_IN_TEXT_RE.findall(str(text or ""))
    ]


def _fmt(number):
    return str(int(number)) if float(number).is_integer() else f"{number:g}"


def display_size(text):
    """Normalised size like "60×60 cm", or None if the size is unclear."""
    cm = size_in_cm(text)
    if not cm:
        return None
    return f"{_fmt(cm[0])}×{_fmt(cm[1])} cm"


def same_size(a, b, tolerance_cm=3.0):
    """True if two (cm, cm) sizes match in either orientation (2×2 ft ≈ 60×60 cm)."""
    return (
        (abs(a[0] - b[0]) <= tolerance_cm and abs(a[1] - b[1]) <= tolerance_cm)
        or (abs(a[0] - b[1]) <= tolerance_cm and abs(a[1] - b[0]) <= tolerance_cm)
    )

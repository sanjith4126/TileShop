"""
Small shared helpers.
"""

# Largest id we accept from a URL or form; anything bigger can't be a real row
# and would overflow SQLite's integer type.
MAX_ID = 2**31 - 1


def parse_positive_int(value):
    """Return ``value`` as an int greater than zero, or None for anything else."""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if 0 < number <= MAX_ID:
        return number
    return None

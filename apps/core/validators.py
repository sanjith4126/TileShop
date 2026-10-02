"""
Form validators shared by the quote and checkout forms.
"""
import re

from django import forms

_PHONE_CHARS = re.compile(r"^\+?[\d\s\-()]+$")


def clean_phone_number(value):
    """Accept common phone formats ("+91 98765 43210", "0424-2234567") with 7–15 digits."""
    value = " ".join((value or "").split())
    digit_count = len(re.sub(r"\D", "", value))
    if not _PHONE_CHARS.match(value) or not 7 <= digit_count <= 15:
        raise forms.ValidationError("Please enter a valid phone number.")
    return value


def clean_single_line(value):
    """Collapse whitespace (including newlines) in short text fields."""
    return " ".join((value or "").split())

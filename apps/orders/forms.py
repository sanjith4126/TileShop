"""
Orders forms.
"""
from django import forms

from apps.core.validators import clean_phone_number, clean_single_line

from .models import Order


class CheckoutForm(forms.Form):
    """Delivery details for a pay-on-delivery order."""

    full_name = forms.CharField(max_length=200, error_messages={"required": "Please enter your name."})
    email = forms.EmailField(
        max_length=254,
        error_messages={
            "required": "Please enter your email address.",
            "invalid": "Please enter a valid email address.",
        },
    )
    phone = forms.CharField(max_length=20, error_messages={"required": "Please enter your phone number."})
    shipping_address = forms.CharField(
        max_length=1000,
        widget=forms.Textarea,
        error_messages={"required": "Please enter your delivery address."},
    )
    payment_method = forms.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, initial="cash")
    notes = forms.CharField(max_length=1000, required=False, widget=forms.Textarea)

    def clean_full_name(self):
        return clean_single_line(self.cleaned_data.get("full_name"))

    def clean_phone(self):
        return clean_phone_number(self.cleaned_data.get("phone"))

    def clean_shipping_address(self):
        return (self.cleaned_data.get("shipping_address") or "").strip()

    def clean_notes(self):
        return (self.cleaned_data.get("notes") or "").strip()

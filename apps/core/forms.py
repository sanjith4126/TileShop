"""
Core app forms.
"""
from django import forms

from .models import Inquiry
from .validators import clean_phone_number, clean_single_line


class InquiryForm(forms.ModelForm):
    """Quote / contact request. The linked product is set by the view."""

    class Meta:
        model = Inquiry
        fields = [
            "full_name",
            "email",
            "phone",
            "address",
            "referrer_type",
            "referrer_name",
            "tile_interest",
            "area_sqft",
            "project_type",
            "message",
        ]
        error_messages = {
            "full_name": {"required": "Please enter your name."},
            "email": {
                "required": "Please enter your email address.",
                "invalid": "Please enter a valid email address.",
            },
            "phone": {"required": "Please enter your phone number."},
        }

    def clean_full_name(self):
        return clean_single_line(self.cleaned_data.get("full_name"))

    def clean_phone(self):
        return clean_phone_number(self.cleaned_data.get("phone"))

    def clean_address(self):
        return clean_single_line(self.cleaned_data.get("address"))

    def clean_referrer_name(self):
        return clean_single_line(self.cleaned_data.get("referrer_name"))

    def clean_tile_interest(self):
        return clean_single_line(self.cleaned_data.get("tile_interest"))

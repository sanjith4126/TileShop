"""
Quote requests are saved, validated and (optionally) emailed to the shop (A1).
"""
from django.core import mail
from django.test import override_settings

from apps.core.models import Inquiry

from .base import ShopTestCase

VALID = {
    "full_name": "S. Karthikeyan",
    "email": "karthik@example.com",
    "phone": "+91 98765 11111",
    "address": "Salem",
    "referrer_type": "mason",
    "referrer_name": "Murugan",
    "area_sqft": "450",
    "project_type": "residential",
    "message": "Kitchen floor and wall.",
}


class InquiryTests(ShopTestCase):
    def test_valid_request_is_saved_with_product(self):
        response = self.client.post("/inquiry/", {**VALID, "product_id": self.product.pk})
        self.assertRedirects(response, "/inquiry/")
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.full_name, "S. Karthikeyan")
        self.assertEqual(inquiry.product, self.product)
        self.assertEqual(inquiry.tile_interest, "Myglamm Grey")
        self.assertEqual(inquiry.area_sqft, 450)
        self.assertEqual(inquiry.referrer_type, "mason")
        self.assertEqual(inquiry.status, "new")

    def test_confirmation_is_shown_once(self):
        self.client.post("/inquiry/", VALID)
        first = self.client.get("/inquiry/")
        self.assertContains(first, "Quote Request Submitted!")
        second = self.client.get("/inquiry/")
        self.assertNotContains(second, "Quote Request Submitted!")
        # The old ?submitted=1 trick no longer shows a fake confirmation.
        self.assertNotContains(self.client.get("/inquiry/?submitted=1"), "Quote Request Submitted!")

    def test_invalid_request_shows_errors_and_keeps_input(self):
        response = self.client.post("/inquiry/", {**VALID, "phone": "call me", "email": "not-an-email"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertContains(response, "Please enter a valid phone number.")
        self.assertContains(response, "Please enter a valid email address.")
        self.assertContains(response, 'value="S. Karthikeyan"')

    def test_bad_product_parameter_does_not_crash(self):
        for value in ("abc", "-1", "99999999999999999999", "0"):
            self.assertEqual(self.client.get(f"/inquiry/?product={value}").status_code, 200)

    def test_inactive_product_is_not_linked(self):
        self.client.post("/inquiry/", {**VALID, "product_id": self.inactive.pk})
        self.assertIsNone(Inquiry.objects.get().product)

    def test_labels_are_connected_to_inputs(self):
        response = self.client.get("/inquiry/")
        for field in ("full_name", "email", "phone", "address", "area_sqft", "project_type", "message"):
            self.assertContains(response, f'for="id_{field}"')
            self.assertContains(response, f'id="id_{field}"')

    def test_no_email_without_configuration(self):
        self.client.post("/inquiry/", VALID)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(SHOP_NOTIFICATION_EMAIL="shop@example.com")
    def test_shop_is_emailed_when_configured(self):
        self.client.post("/inquiry/", {**VALID, "product_id": self.product.pk})
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["shop@example.com"])
        self.assertIn("S. Karthikeyan", message.subject)
        self.assertIn("+91 98765 11111", message.body)
        self.assertIn("Myglamm Grey", message.body)

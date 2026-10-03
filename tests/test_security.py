"""
Security fixes: order privacy (A2), open redirect (A5), POST-only logout (A18),
no admin link for customers (A8), brand name (A16).
"""
import os
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase

from apps.orders.models import Order, OrderItem
from tileshop.settings import _env_bool

from .base import ShopTestCase


def make_order(product, user=None):
    order = Order.objects.create(
        user=user, full_name="Meera Iyer", email="meera@example.com", phone="+91 90000 00000",
        shipping_address="12 Main Road, Bhavani", payment_method="cash", total_price=Decimal("520.00"),
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=product.price)
    return order


class OrderPrivacyTests(ShopTestCase):
    def test_strangers_cannot_open_an_order_confirmation(self):
        order = make_order(self.product)
        response = self.client.get(f"/orders/success/{order.pk}/")
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "12 Main Road", status_code=404)

    def test_the_browser_that_placed_the_order_can_see_it(self):
        self.add_to_cart(self.product)
        response = self.client.post("/orders/checkout/", {
            "full_name": "Rahul V", "email": "rahul@example.com", "phone": "+91 98400 12345",
            "shipping_address": "5 Temple Street, Erode", "payment_method": "upi",
        })
        order = Order.objects.get()
        self.assertRedirects(response, f"/orders/success/{order.pk}/")
        page = self.client.get(f"/orders/success/{order.pk}/")
        self.assertContains(page, "5 Temple Street")
        self.assertContains(page, f"#{order.order_number}")
        self.assertContains(page, '<meta name="robots" content="noindex,nofollow"', html=False)

    def test_account_owner_can_see_their_order_but_others_cannot(self):
        owner = User.objects.create_user("owner", password="pass-12345-word")
        User.objects.create_user("other", password="pass-12345-word")
        order = make_order(self.product, user=owner)

        self.client.login(username="other", password="pass-12345-word")
        self.assertEqual(self.client.get(f"/orders/success/{order.pk}/").status_code, 404)
        self.assertEqual(self.client.get(f"/orders/{order.pk}/").status_code, 404)

        self.client.login(username="owner", password="pass-12345-word")
        self.assertEqual(self.client.get(f"/orders/success/{order.pk}/").status_code, 200)
        detail = self.client.get(f"/orders/{order.pk}/")
        self.assertContains(detail, "12 Main Road")

    def test_order_detail_requires_login(self):
        order = make_order(self.product)
        response = self.client.get(f"/orders/{order.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_dashboard_links_to_order_details(self):
        owner = User.objects.create_user("owner", password="pass-12345-word")
        order = make_order(self.product, user=owner)
        self.client.login(username="owner", password="pass-12345-word")
        response = self.client.get("/accounts/dashboard/")
        self.assertContains(response, f'href="/orders/{order.pk}/"')
        self.assertContains(response, f"#{order.order_number}")
        self.assertNotContains(response, 'href="#"')


class LoginRedirectTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        User.objects.create_user("buyer", password="pass-12345-word")

    def login(self, next_url):
        return self.client.post(
            f"/accounts/login/?next={next_url}", {"username": "buyer", "password": "pass-12345-word"}
        )

    def test_external_next_url_is_ignored(self):
        for target in ("https://evil.example/", "//evil.example/", "http://evil.example/phish"):
            self.client.logout()
            response = self.login(target)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], "/accounts/dashboard/", target)

    def test_local_next_url_is_followed(self):
        response = self.login("/products/")
        self.assertEqual(response["Location"], "/products/")

    def test_no_admin_link_on_login_page(self):
        response = self.client.get("/accounts/login/")
        self.assertNotContains(response, "/admin/")
        self.assertContains(response, "<h1", html=False)


class LogoutTests(ShopTestCase):
    def test_get_does_not_log_out(self):
        User.objects.create_user("buyer", password="pass-12345-word")
        self.client.login(username="buyer", password="pass-12345-word")
        self.client.get("/accounts/logout/")
        self.assertEqual(self.client.get("/accounts/dashboard/").status_code, 200)

    def test_post_logs_out(self):
        User.objects.create_user("buyer", password="pass-12345-word")
        self.client.login(username="buyer", password="pass-12345-word")
        self.client.post("/accounts/logout/")
        self.assertEqual(self.client.get("/accounts/dashboard/").status_code, 302)


class BrandTests(ShopTestCase):
    def test_register_welcome_uses_brand_name(self):
        response = self.client.post("/accounts/register/", {
            "username": "newbuyer", "password1": "Tiles-Bhavani-2026", "password2": "Tiles-Bhavani-2026",
        }, follow=True)
        self.assertContains(response, "Welcome to Suwasthick Tiles")
        self.assertNotContains(response, "TileShop Premium")


class EnvironmentSettingTests(SimpleTestCase):
    def test_empty_boolean_variables_use_the_default(self):
        """'EMAIL_USE_TLS=' copied empty from .env.example must not switch TLS off."""
        with mock.patch.dict(os.environ, {"TILESHOP_TEST_FLAG": ""}):
            self.assertTrue(_env_bool("TILESHOP_TEST_FLAG", "True"))
            self.assertFalse(_env_bool("TILESHOP_TEST_FLAG", "False"))
        with mock.patch.dict(os.environ, {"TILESHOP_TEST_FLAG": "off"}):
            self.assertFalse(_env_bool("TILESHOP_TEST_FLAG", "True"))
        with mock.patch.dict(os.environ, {"TILESHOP_TEST_FLAG": " yes "}):
            self.assertTrue(_env_bool("TILESHOP_TEST_FLAG", "False"))

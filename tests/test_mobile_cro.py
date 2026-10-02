"""
Conversion and mobile details: things that worked only with a mouse, limits the
page and the cart disagreed on, and how long a cart is kept.
"""
import re

from django.conf import settings
from django.test import override_settings

from .base import ShopTestCase


class MobileAndConversionTests(ShopTestCase):
    def test_cart_session_lasts_two_weeks(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 60 * 60 * 24 * 14)

    def test_home_category_names_do_not_need_hover(self):
        html = self.client.get("/").content.decode()
        labels = re.findall(r'<div class="absolute bottom-0 left-0[^"]*"', html)
        self.assertTrue(labels)
        for label in labels:
            # Hidden until hover only on devices that can hover; always shown on touch screens.
            self.assertNotRegex(label, r'[" ]translate-y-full')
            self.assertIn("[@media(hover:hover)]:translate-y-full", label)

    def test_mobile_menu_is_not_trapped_inside_the_header(self):
        html = self.client.get("/").content.decode()
        nav_classes = re.search(r'<nav id="main-nav" class="([^"]*)"', html).group(1).split()
        # A backdrop blur, filter or transform on the header turns it into the containing
        # block of the fixed full-screen menu, which then collapses to the header's height.
        for name in nav_classes:
            self.assertFalse(name.startswith(("backdrop-", "blur", "filter", "transform")), name)
        self.assertIn('id="mobile-menu"', html)

    def test_product_quantity_limit_matches_the_cart(self):
        url = self.product.get_absolute_url()
        html = self.client.get(url).content.decode()
        self.assertIn(f'max="{settings.MAX_CART_QUANTITY}"', html)
        with override_settings(ENFORCE_STOCK_LIMITS=True):
            html = self.client.get(url).content.decode()
        self.assertIn(f'max="{self.product.stock}"', html)

    def test_quantity_buttons_are_finger_sized(self):
        html = self.client.get(self.product.get_absolute_url()).content.decode()
        for label in ("Decrease quantity", "Increase quantity"):
            button = re.search(rf'<button [^>]*aria-label="{label}"[^>]*>', html).group(0)
            self.assertIn("w-11", button)  # 44px wide

    def test_flash_message_close_button(self):
        self.add_to_cart(self.product)
        html = self.client.get("/cart/").content.decode()
        button = re.search(r'<button [^>]*aria-label="Dismiss message"[^>]*>', html)
        self.assertIsNotNone(button)
        self.assertIn('type="button"', button.group(0))

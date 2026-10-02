"""
Management commands (seo_audit, clear_stale_carts) and keeping the cart when a
visitor signs in or registers.
"""
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.content.models import Page
from apps.orders.models import Order
from apps.products.models import Product

from .base import ShopTestCase


def run(command, *args):
    out = StringIO()
    call_command(command, *args, stdout=out)
    return out.getvalue()


class SeoAuditTests(ShopTestCase):
    def section(self, report, title):
        """The lines listed under one check of the report."""
        lines = report.splitlines()
        start = next(i for i, line in enumerate(lines) if title in line)
        items = []
        for line in lines[start + 1:]:
            if not line.startswith("      - "):
                break
            items.append(line.strip("- ").strip())
        return items

    def test_reports_catalogue_gaps(self):
        report = run("seo_audit")
        self.assertEqual(self.section(report, "Not in any category"), ["LUXE GREY"])
        self.assertIn("ALTROZ GREY: '4/2'", self.section(report, "Unclear size"))
        self.assertIn("SCONE YELLOW", self.section(report, "No size"))
        self.assertIn("LUXE GREY", self.section(report, "No main image"))
        self.assertIn("JUNGLE LUSH (12 characters)", self.section(report, "thin description"))
        self.assertEqual(self.section(report, "Empty: no active products"), ["Wall Tiles"])
        self.assertIn("Not confirmed", report)
        self.assertNotIn("Discontinued Tile", report)  # inactive products are not checked

    def test_reports_duplicate_titles_and_unreviewed_placeholders(self):
        Product.objects.create(name="Myglamm Grey", description="x" * 80, price=Decimal("10"),
                               material="porcelain", size="60x60cm", category=self.floor)
        Page.objects.filter(slug="warranty").update(is_published=True)
        report = run("seo_audit")
        self.assertTrue(self.section(report, "Duplicate product names"))
        self.assertTrue(self.section(report, "Pages with the same title"))
        self.assertEqual(self.section(report, "[OWNER TO CONFIRM] still in the text"), ["Warranty"])

    def test_is_read_only_and_can_fail_the_build(self):
        before = (Product.objects.count(), Page.objects.filter(is_published=True).count())
        with self.assertRaises(CommandError):
            call_command("seo_audit", "--fail-on-issues", stdout=StringIO())
        self.assertEqual(before, (Product.objects.count(), Page.objects.filter(is_published=True).count()))


class ClearStaleCartsTests(ShopTestCase):
    def test_deletes_only_carts_without_a_live_session(self):
        self.add_to_cart(self.product)  # a real visitor with a live session
        live = Cart.objects.get()
        orphan = Cart.objects.create(session_id="no-such-session")
        expired_session = SessionStore()
        expired_session.create()
        expired_session_model = expired_session.model.objects.get(session_key=expired_session.session_key)
        expired_session_model.expire_date = timezone.now() - timedelta(days=1)
        expired_session_model.save()
        expired = Cart.objects.create(session_id=expired_session.session_key)
        CartItem.objects.create(cart=expired, product=self.product, quantity=2)
        order = Order.objects.create(full_name="A", email="a@example.com", phone="9876500000",
                                     shipping_address="Bhavani", total_price=Decimal("520"))

        self.assertIn("2 stale cart(s) would be deleted", run("clear_stale_carts", "--dry-run"))
        self.assertEqual(Cart.objects.count(), 3)

        self.assertIn("Deleted 2 stale cart(s)", run("clear_stale_carts"))
        self.assertEqual(list(Cart.objects.all()), [live])
        self.assertFalse(Cart.objects.filter(pk__in=[orphan.pk, expired.pk]).exists())
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())


class CartSurvivesSignInTests(ShopTestCase):
    def cart_contents(self):
        """{product name: quantity} in the cart of the client's current session."""
        session_key = self.client.session.session_key
        items = CartItem.objects.filter(cart__session_id=session_key).select_related("product")
        return {item.product.name: item.quantity for item in items}

    def test_signing_in_keeps_the_cart(self):
        User.objects.create_user("meena", password="tile-pass-2026")
        self.add_to_cart(self.product, 3)
        old_key = self.client.session.session_key
        response = self.client.post("/accounts/login/", {"username": "meena", "password": "tile-pass-2026"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.session.session_key, old_key)  # Django rotates the key on login
        self.assertEqual(self.cart_contents(), {"Myglamm Grey": 3})
        self.assertEqual(self.client.get("/cart/").context["cart_count"], 3)

    def test_registering_keeps_the_cart(self):
        self.add_to_cart(self.bath_product)
        response = self.client.post("/accounts/register/", {
            "username": "ravi", "password1": "tile-pass-2026!", "password2": "tile-pass-2026!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.cart_contents(), {"JUNGLE LUSH": 1})

    def test_logging_out_empties_the_cart(self):
        User.objects.create_user("meena", password="tile-pass-2026")
        self.client.post("/accounts/login/", {"username": "meena", "password": "tile-pass-2026"})
        self.add_to_cart(self.product)
        self.assertEqual(self.cart_contents(), {"Myglamm Grey": 1})
        self.client.post("/accounts/logout/")
        self.assertEqual(self.cart_contents(), {})
        self.assertEqual(self.client.get("/cart/").context["cart_count"], 0)

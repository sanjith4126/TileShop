"""
Cart input validation (A6), checkout validation and atomic orders (A10).
"""
from django.core import mail
from django.test import override_settings

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order

from .base import ShopTestCase

CHECKOUT = {
    "full_name": "Rahul Vishwanath",
    "email": "rahul@example.com",
    "phone": "+91 98400 12345",
    "shipping_address": "5 Temple Street, Erode 638001",
    "payment_method": "upi",
    "notes": "Call before delivery",
}


class CartInputTests(ShopTestCase):
    def test_add_and_view_cart(self):
        self.add_to_cart(self.product, 3)
        response = self.client.get("/cart/")
        self.assertContains(response, "Myglamm Grey")
        self.assertEqual(response.context["cart_items_count"], 3)
        self.assertEqual(response.context["cart_total"], self.product.price * 3)

    def test_invalid_quantities_never_crash(self):
        for bad in ("abc", "-5", "0", "", "1.5", "99999999999999999999999"):
            response = self.add_to_cart(self.product, bad)
            self.assertEqual(response.status_code, 302, bad)
        self.assertFalse(CartItem.objects.filter(quantity__lte=0).exists())

    def test_quantity_is_capped(self):
        with self.settings(MAX_CART_QUANTITY=500):
            self.add_to_cart(self.product, 400)
            self.add_to_cart(self.product, 400)
        self.assertEqual(CartItem.objects.get().quantity, 500)

    @override_settings(ENFORCE_STOCK_LIMITS=True)
    def test_stock_limit_when_enforced(self):
        self.add_to_cart(self.product, 1000)
        self.assertEqual(CartItem.objects.get().quantity, self.product.stock)

    def test_out_of_stock_and_inactive_products_cannot_be_added(self):
        self.add_to_cart(self.out_of_stock, 1)
        self.assertFalse(CartItem.objects.exists())
        self.assertEqual(self.add_to_cart(self.inactive, 1).status_code, 404)

    def test_update_cart_with_bad_input(self):
        self.add_to_cart(self.product, 2)
        item = CartItem.objects.get()
        self.assertEqual(self.client.post(f"/cart/update/{item.pk}/", {"quantity": "lots"}).status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.client.post(f"/cart/update/{item.pk}/", {"quantity": "0"})
        self.assertFalse(CartItem.objects.exists())

    def test_cannot_touch_someone_elses_cart_item(self):
        self.add_to_cart(self.product, 2)
        item = CartItem.objects.get()
        stranger = self.client_class()
        stranger.get("/")  # no session cookie of the first visitor
        self.assertEqual(stranger.post(f"/cart/remove/{item.pk}/").status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_viewing_cart_does_not_create_carts(self):
        self.client.get("/cart/")
        self.assertFalse(Cart.objects.exists())

    def test_cart_page_is_noindex(self):
        self.assertContains(self.client.get("/cart/"), 'content="noindex,nofollow"')


class CheckoutTests(ShopTestCase):
    def test_empty_cart_redirects_to_cart(self):
        self.assertRedirects(self.client.get("/orders/checkout/"), "/cart/")

    def test_invalid_details_show_errors_and_keep_input(self):
        self.add_to_cart(self.product)
        response = self.client.post("/orders/checkout/", {**CHECKOUT, "phone": "12", "shipping_address": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "Please enter a valid phone number.")
        self.assertContains(response, "Please enter your delivery address.")
        self.assertContains(response, 'value="Rahul Vishwanath"')

    def test_invalid_payment_method_is_rejected(self):
        self.add_to_cart(self.product)
        self.client.post("/orders/checkout/", {**CHECKOUT, "payment_method": "bitcoin"})
        self.assertEqual(Order.objects.count(), 0)

    def test_successful_checkout(self):
        self.add_to_cart(self.product, 2)
        self.add_to_cart(self.bath_product, 10)
        response = self.client.post("/orders/checkout/", CHECKOUT)
        order = Order.objects.get()
        self.assertRedirects(response, f"/orders/success/{order.pk}/")
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_price, self.product.price * 2 + self.bath_product.price * 10)
        self.assertEqual(order.payment_method, "upi")
        self.assertEqual(order.order_number, f"ST-{order.pk}")
        self.assertFalse(CartItem.objects.exists())

    def test_inactive_items_are_removed_before_ordering(self):
        self.add_to_cart(self.product)
        type(self.product).objects.filter(pk=self.product.pk).update(is_active=False)
        response = self.client.post("/orders/checkout/", CHECKOUT)
        self.assertRedirects(response, "/cart/", fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(), 0)
        self.assertFalse(CartItem.objects.exists())

    @override_settings(SHOP_NOTIFICATION_EMAIL="shop@example.com")
    def test_shop_is_emailed_about_new_orders(self):
        self.add_to_cart(self.product)
        self.client.post("/orders/checkout/", CHECKOUT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New order #ST-", mail.outbox[0].subject)
        self.assertIn("5 Temple Street", mail.outbox[0].body)

    @override_settings(ENFORCE_STOCK_LIMITS=True)
    def test_stock_is_decremented_when_enforced(self):
        self.add_to_cart(self.product, 5)
        self.client.post("/orders/checkout/", CHECKOUT)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 145)

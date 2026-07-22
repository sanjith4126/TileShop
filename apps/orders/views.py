"""
Orders views — checkout (no online payment) and order confirmation.

Payment is collected at the time of delivery (UPI / Card / Cheque / Cash).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Order, OrderItem
from apps.cart.views import get_or_create_cart


def checkout(request):
    """Collect delivery details and place an order — no online payment."""
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product").all()

    if not items:
        messages.info(request, "Your cart is empty. Add some tiles before placing an order.")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("shipping_address", "").strip()
        payment_method = request.POST.get("payment_method", "cash").strip()
        notes = request.POST.get("notes", "").strip()

        valid_methods = dict(Order.PAYMENT_METHOD_CHOICES)
        if payment_method not in valid_methods:
            payment_method = "cash"

        if full_name and email and phone and address:
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=full_name,
                email=email,
                phone=phone,
                shipping_address=address,
                payment_method=payment_method,
                notes=notes,
                status="pending",
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                )
            order.calculate_total()

            # Clear the cart
            cart.items.all().delete()

            return redirect("orders:order_success", order_id=order.pk)

        messages.error(request, "Please fill in your name, email, phone and delivery address.")

    context = {
        "cart": cart,
        "items": items,
        "payment_methods": Order.PAYMENT_METHOD_CHOICES,
    }
    return render(request, "orders/checkout.html", context)


def order_success(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, pk=order_id)
    context = {
        "order": order,
        "items": order.items.select_related("product").all(),
    }
    return render(request, "orders/order_success.html", context)

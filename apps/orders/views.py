"""
Orders views — checkout (no online payment), order confirmation and order details.

Payment is collected at the time of delivery (UPI / Card / Cheque / Cash).
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse

from apps.cart.views import cart_summary, get_cart
from apps.core.notifications import notify_shop
from apps.core.seo import NOINDEX_NOFOLLOW, page_meta
from apps.products.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem

SESSION_ORDERS_KEY = "placed_orders"


class OutOfStock(Exception):
    pass


def _remember_order(request, order):
    """Let this browser see its own order confirmation (and nobody else's)."""
    placed = [pk for pk in request.session.get(SESSION_ORDERS_KEY, []) if pk != order.pk]
    request.session[SESSION_ORDERS_KEY] = (placed + [order.pk])[-20:]


def checkout(request):
    """Collect delivery details and place an order — no online payment."""
    cart = get_cart(request)
    items = list(cart.items.select_related("product")) if cart else []

    if not items:
        messages.info(request, "Your cart is empty. Add some tiles before placing an order.")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            unavailable = [item for item in items if not item.product.is_active or item.quantity < 1]
            if unavailable:
                for item in unavailable:
                    item.delete()
                messages.error(
                    request,
                    "Some items are no longer available and were removed from your cart. "
                    "Please review your order.",
                )
                return redirect("cart:cart_detail")

            try:
                order = _place_order(request, cart, items, form.cleaned_data)
            except OutOfStock as exc:
                messages.error(request, f'Sorry, there isn\'t enough stock of "{exc}". Please adjust your cart.')
                return redirect("cart:cart_detail")

            _remember_order(request, order)
            _notify_new_order(request, order)
            return redirect("orders:order_success", order_id=order.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"full_name": request.user.get_full_name(), "email": request.user.email}
        form = CheckoutForm(initial=initial)

    context = {
        "cart": cart,
        "items": items,
        "form": form,
        "payment_methods": Order.PAYMENT_METHOD_CHOICES,
        **cart_summary(items),
        "seo": page_meta(request, "Place Your Order", robots=NOINDEX_NOFOLLOW),
    }
    return render(request, "orders/checkout.html", context)


def _place_order(request, cart, items, data):
    """Create the order and its items in one transaction, then empty the cart."""
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            shipping_address=data["shipping_address"],
            payment_method=data["payment_method"],
            notes=data["notes"],
            status="pending",
            total_price=sum(item.product.price * item.quantity for item in items),
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=item.product, quantity=item.quantity, unit_price=item.product.price)
            for item in items
        ])
        if settings.ENFORCE_STOCK_LIMITS:
            for item in items:
                updated = Product.objects.filter(pk=item.product_id, stock__gte=item.quantity).update(
                    stock=F("stock") - item.quantity
                )
                if not updated:
                    raise OutOfStock(item.product.name)
        cart.items.all().delete()
    return order


def _notify_new_order(request, order):
    lines = [
        f"Order: #{order.order_number}",
        f"Name: {order.full_name}",
        f"Phone: {order.phone}",
        f"Email: {order.email}",
        f"Payment: {order.get_payment_method_display()}",
        "Delivery address:",
        order.shipping_address,
        "",
        "Items:",
    ]
    lines += [
        f"- {item.quantity} x {item.product.name} @ Rs.{item.unit_price} = Rs.{item.subtotal}"
        for item in order.items.select_related("product")
    ]
    lines.append(f"Total: Rs.{order.total_price}")
    if order.notes:
        lines += ["", f"Notes: {order.notes}"]
    try:
        lines += ["", "Open in admin: " + request.build_absolute_uri(
            reverse("admin:orders_order_change", args=[order.pk])
        )]
    except NoReverseMatch:
        pass
    notify_shop(f"New order #{order.order_number} from {order.full_name}", "\n".join(lines))


def order_success(request, order_id):
    """Order confirmation — only for the browser that placed it, or its account owner."""
    order = get_object_or_404(Order, pk=order_id)
    placed_here = order.pk in request.session.get(SESSION_ORDERS_KEY, [])
    owns_it = request.user.is_authenticated and order.user_id == request.user.id
    if not (placed_here or owns_it):
        raise Http404("Order not found")
    context = {
        "order": order,
        "items": order.items.select_related("product").all(),
        "seo": page_meta(request, "Order Confirmed", robots=NOINDEX_NOFOLLOW),
    }
    return render(request, "orders/order_success.html", context)


@login_required
def order_detail(request, order_id):
    """Order details for the logged-in customer who placed the order."""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    context = {
        "order": order,
        "items": order.items.select_related("product").all(),
        "seo": page_meta(request, f"Order #{order.order_number}", robots=NOINDEX_NOFOLLOW),
    }
    return render(request, "orders/order_detail.html", context)

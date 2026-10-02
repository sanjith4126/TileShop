"""
Cart views - session-based cart management.
"""
from django.conf import settings
from django.contrib import messages
from django.db.models import Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.seo import NOINDEX_NOFOLLOW, page_meta
from apps.core.utils import parse_positive_int
from apps.products.models import Product

from .models import Cart, CartItem


def get_or_create_cart(request):
    """Get or create a cart for the current session."""
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def get_cart(request):
    """The current session's cart, or None. Never creates a session or cart."""
    session_id = request.session.session_key
    if not session_id:
        return None
    return Cart.objects.filter(session_id=session_id).first()


def cart_summary(items):
    """Total price and item count for already-fetched cart items."""
    return {
        "cart_total": sum(item.subtotal for item in items),
        "cart_items_count": sum(item.quantity for item in items),
    }


def max_quantity(product):
    """Largest quantity of ``product`` allowed in one cart line."""
    limit = settings.MAX_CART_QUANTITY
    if settings.ENFORCE_STOCK_LIMITS:
        limit = min(limit, product.stock)
    return limit


def cart_detail(request):
    """Display cart contents."""
    cart = get_cart(request)
    items = list(cart.items.select_related("product", "product__category")) if cart else []
    context = {
        "cart": cart,
        "items": items,
        **cart_summary(items),
        "seo": page_meta(request, "Your Cart", robots=NOINDEX_NOFOLLOW),
    }
    return render(request, "cart/cart.html", context)


def _cart_response(request, ok, message, cart=None):
    """JSON for AJAX callers, otherwise a flash message and a redirect to the cart."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        count = 0
        if cart is not None:
            count = cart.items.aggregate(total=Sum("quantity"))["total"] or 0
        return JsonResponse({"success": ok, "cart_count": count, "message": message}, status=200 if ok else 400)
    (messages.success if ok else messages.error)(request, message)
    return redirect("cart:cart_detail")


@require_POST
def add_to_cart(request, product_id):
    """Add a product to the cart or increment quantity."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = parse_positive_int(request.POST.get("quantity", 1))
    if quantity is None:
        return _cart_response(request, False, "Please enter a valid quantity.")
    if product.stock <= 0:
        return _cart_response(request, False, f'"{product.name}" is out of stock.')

    cart = get_or_create_cart(request)
    cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 0})
    wanted = cart_item.quantity + quantity
    cart_item.quantity = min(wanted, max_quantity(product))
    cart_item.save()

    if cart_item.quantity < wanted:
        message = f'"{product.name}": quantity limited to {cart_item.quantity}.'
    else:
        message = f'"{product.name}" added to cart.'
    return _cart_response(request, True, message, cart)


@require_POST
def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    cart = get_cart(request)
    if cart is None:
        raise Http404("No cart")
    cart_item = get_object_or_404(CartItem.objects.select_related("product"), pk=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'"{product_name}" removed from cart.')
    return redirect("cart:cart_detail")


@require_POST
def update_cart(request, item_id):
    """Update quantity of a cart item. A quantity below 1 removes it."""
    cart = get_cart(request)
    if cart is None:
        raise Http404("No cart")
    cart_item = get_object_or_404(CartItem.objects.select_related("product"), pk=item_id, cart=cart)
    try:
        quantity = int(str(request.POST.get("quantity", "")).strip())
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("cart:cart_detail")

    if quantity < 1:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    else:
        limit = max_quantity(cart_item.product)
        cart_item.quantity = min(quantity, limit)
        cart_item.save()
        if quantity > limit:
            messages.info(request, f"Quantity limited to {limit}.")
        else:
            messages.success(request, "Cart updated.")
    return redirect("cart:cart_detail")

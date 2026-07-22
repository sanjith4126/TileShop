"""
Cart views - session-based cart management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Cart, CartItem
from apps.products.models import Product


def get_or_create_cart(request):
    """Get or create a cart for the current session."""
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def cart_detail(request):
    """Display cart contents."""
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product").all()
    context = {
        "cart": cart,
        "items": items,
    }
    return render(request, "cart/cart.html", context)


@require_POST
def add_to_cart(request, product_id):
    """Add a product to the cart or increment quantity."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get("quantity", 1))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f'"{product.name}" added to cart.')

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "cart_count": cart.total_items,
            "message": f'"{product.name}" added to cart.',
        })

    return redirect("cart:cart_detail")


@require_POST
def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'"{product_name}" removed from cart.')
    return redirect("cart:cart_detail")


@require_POST
def update_cart(request, item_id):
    """Update quantity of a cart item."""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    quantity = int(request.POST.get("quantity", 1))
    if quantity < 1:
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated.")
    return redirect("cart:cart_detail")

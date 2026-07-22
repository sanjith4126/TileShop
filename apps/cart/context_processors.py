"""
Cart context processor - makes cart count available in all templates.
"""
from .models import Cart


def cart_count(request):
    """Add cart item count to template context."""
    count = 0
    if request.session.session_key:
        try:
            cart = Cart.objects.get(session_id=request.session.session_key)
            count = cart.total_items
        except Cart.DoesNotExist:
            count = 0
    return {"cart_count": count}

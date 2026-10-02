"""
Cart context processor - makes cart count available in all templates.
"""
from django.db.models import Sum

from .models import CartItem


def cart_count(request):
    """Add the number of items in the visitor's cart (one query, none without a session)."""
    count = 0
    session_key = request.session.session_key
    if session_key:
        count = (
            CartItem.objects.filter(cart__session_id=session_key)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
    return {"cart_count": count}

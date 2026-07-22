"""
Cart admin configuration.
"""
from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["subtotal"]

    def subtotal(self, obj):
        return f"₹{obj.subtotal:.2f}"
    subtotal.short_description = "Subtotal"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["session_id", "total_items", "total_price", "created_at"]
    inlines = [CartItemInline]
    readonly_fields = ["session_id", "created_at", "updated_at"]

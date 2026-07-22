"""
Orders admin.
"""
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["subtotal"]

    def subtotal(self, obj):
        if not obj.pk or obj.unit_price is None:
            return "—"
        return f"₹{obj.subtotal:.2f}"
    subtotal.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "phone", "status", "payment_method", "total_price", "created_at"]
    list_filter = ["status", "payment_method", "created_at"]
    search_fields = ["full_name", "email", "phone", "user__username", "user__email"]
    list_editable = ["status"]
    inlines = [OrderItemInline]
    readonly_fields = ["created_at", "updated_at"]

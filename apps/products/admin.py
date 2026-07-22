"""
Products admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """Add 2–4 extra design / fitted-room photos per product."""
    model = ProductImage
    extra = 3
    fields = ["preview", "image", "caption", "order"]
    readonly_fields = ["preview"]

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:4px;"/>',
                obj.image.url,
            )
        return "—"
    preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "thumb", "name", "category", "price", "is_featured", "is_active",
        "stock", "created_at"
    ]
    list_display_links = ["name"]
    list_filter = ["is_featured", "is_active", "category", "additional_categories"]
    list_editable = ["is_featured", "is_active", "price", "stock"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "image_preview"]
    filter_horizontal = ["additional_categories"]
    inlines = [ProductImageInline]
    actions = ["delete_main_image"]
    fieldsets = (
        ("Product Info", {
            "fields": ("name", "description", "category", "additional_categories",
                       "material", "size", "price", "stock")
        }),
        ("Main Tile Image", {
            "fields": ("image_preview", "image"),
            "description": "The tile swatch. Tick 'Clear' + Save to remove it, "
                           "or use the 'Delete main image' action in the list view.",
        }),
        ("Status", {
            "fields": ("is_featured", "is_active")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:42px;width:42px;object-fit:cover;border-radius:4px;"/>',
                obj.image.url,
            )
        return "—"
    thumb.short_description = ""

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height:160px;border-radius:6px;"/>',
                obj.image.url,
            )
        return "No image uploaded yet."
    image_preview.short_description = "Current image"

    @admin.action(description="🗑 Delete main image of selected products")
    def delete_main_image(self, request, queryset):
        count = 0
        for product in queryset:
            if product.image:
                product.image.delete(save=False)
                product.image = None
                product.save(update_fields=["image"])
                count += 1
        self.message_user(request, f"Deleted the main image of {count} product(s).")

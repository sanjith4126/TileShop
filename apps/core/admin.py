"""
Core app admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Banner, Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Quote requests from the website. Update the status as you follow up."""
    list_display = [
        "created_at", "full_name", "phone", "email", "product", "area_sqft",
        "project_type", "referrer_type", "status",
    ]
    list_display_links = ["full_name"]
    list_editable = ["status"]
    list_filter = ["status", "project_type", "referrer_type", "created_at"]
    list_select_related = ["product"]
    search_fields = ["full_name", "email", "phone", "message", "tile_interest", "referrer_name"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Customer", {"fields": ("full_name", "phone", "email", "address")}),
        ("Project", {"fields": ("product", "tile_interest", "area_sqft", "project_type", "message")}),
        ("Referred by", {"fields": ("referrer_type", "referrer_name")}),
        ("Follow-up", {"fields": ("status", "created_at", "updated_at")}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["thumb", "name", "slug", "created_at"]
    list_display_links = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    readonly_fields = ["image_preview"]
    fields = ["name", "slug", "description", "icon", "image_preview", "image"]
    actions = ["delete_image"]

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:42px;width:42px;object-fit:cover;border-radius:4px;"/>', obj.image.url)
        return "—"
    thumb.short_description = ""

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:160px;border-radius:6px;"/>', obj.image.url)
        return "No image uploaded yet."
    image_preview.short_description = "Current image"

    @admin.action(description="🗑 Delete image of selected categories")
    def delete_image(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.image:
                obj.image.delete(save=False)
                obj.image = None
                obj.save(update_fields=["image"])
                count += 1
        self.message_user(request, f"Deleted the image of {count} category(ies).")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["thumb", "title", "is_active", "order", "created_at"]
    list_display_links = ["title"]
    list_editable = ["is_active", "order"]
    list_filter = ["is_active"]
    readonly_fields = ["image_preview"]
    fields = ["title", "subtitle", "link", "is_active", "order", "image_preview", "image"]
    actions = ["delete_image"]

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:42px;width:72px;object-fit:cover;border-radius:4px;"/>', obj.image.url)
        return "—"
    thumb.short_description = ""

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:160px;border-radius:6px;"/>', obj.image.url)
        return "No image uploaded yet."
    image_preview.short_description = "Current image"

    @admin.action(description="🗑 Delete image of selected banners")
    def delete_image(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.image:
                obj.image.delete(save=False)
                obj.image = None
                obj.save(update_fields=["image"])
                count += 1
        self.message_user(request, f"Deleted the image of {count} banner(s).")

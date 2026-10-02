"""
Core app admin configuration.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .images import delete_renditions
from .models import Category, Banner, BusinessInfo, Inquiry


@admin.register(BusinessInfo)
class BusinessInfoAdmin(admin.ModelAdmin):
    """One record with the shop's contact details. Opens straight to the edit form."""
    fieldsets = (
        ("Shown on the website", {
            "fields": ("address", "phone", "email", "opening_hours", "whatsapp", "maps_url"),
            "description": "These appear in the footer, the About page and the contact page.",
        }),
        ("For Google (structured data)", {
            "fields": ("street_address", "locality", "region", "postal_code", "country",
                       "latitude", "longitude", "opening_hours_spec", "service_areas"),
        }),
        ("Profiles and images", {
            "fields": ("facebook_url", "instagram_url", "youtube_url", "google_business_url", "logo", "share_image"),
        }),
        ("Publish", {
            "fields": ("details_confirmed", "updated_at"),
            "description": (
                "Until this is ticked, the phone and email are shown as plain text and nothing "
                "but the business name is sent to Google."
            ),
        }),
    )
    readonly_fields = ["updated_at"]

    def has_add_permission(self, request):
        return not BusinessInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = BusinessInfo.get_solo()
        return redirect(reverse("admin:core_businessinfo_change", args=[obj.pk]))


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
                delete_renditions(obj.image.name, storage=obj.image.storage)
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
                delete_renditions(obj.image.name, storage=obj.image.storage)
                obj.image.delete(save=False)
                obj.image = None
                obj.save(update_fields=["image"])
                count += 1
        self.message_user(request, f"Deleted the image of {count} banner(s).")

"""
Admin for guides and policy pages.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Guide, Page


class PreviewLinkMixin:
    @admin.display(description="Page")
    def view_link(self, obj):
        if not obj.pk:
            return "—"
        label = "View" if obj.is_published else "Preview draft"
        return format_html('<a href="{}" target="_blank">{}</a>', obj.get_absolute_url(), label)


@admin.register(Page)
class PageAdmin(PreviewLinkMixin, admin.ModelAdmin):
    list_display = ["title", "slug", "is_published", "show_in_footer", "updated_at", "view_link"]
    list_editable = ["is_published", "show_in_footer"]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title", "body"]
    readonly_fields = ["created_at", "updated_at", "view_link"]
    fields = ["title", "slug", "meta_description", "body", "is_published", "show_in_footer",
              "view_link", "created_at", "updated_at"]


@admin.register(Guide)
class GuideAdmin(PreviewLinkMixin, admin.ModelAdmin):
    list_display = ["title", "related_category", "is_published", "published_at", "updated_at", "view_link"]
    list_editable = ["is_published"]
    list_filter = ["is_published", "related_category"]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title", "summary", "body"]
    readonly_fields = ["created_at", "updated_at", "view_link"]
    fields = ["title", "slug", "summary", "body", "cover_image", "author_name", "related_category",
              "is_published", "published_at", "view_link", "created_at", "updated_at"]

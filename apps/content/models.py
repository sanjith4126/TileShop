"""
Owner-editable content: policy pages and guides.

Both start unpublished. The body is HTML written by staff in the admin
(trusted, like Django's flatpages); use <h2>, <p>, <ul>/<li>, <a>, <strong>.
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Category, not_only_digits

BODY_HELP = "HTML. Use <h2> for headings, <p> for paragraphs, <ul><li> for lists, <a href> for links."


class Page(models.Model):
    """Policy and information pages: privacy, terms, delivery, returns, warranty."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, validators=[not_only_digits], help_text="Page address: /policies/<slug>/")
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="One or two sentences for search results (up to 160 characters)."
    )
    body = models.TextField(help_text=BODY_HELP)
    is_published = models.BooleanField(
        default=False, help_text="Only published pages are visible to customers and linked in the footer."
    )
    show_in_footer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:page_detail", kwargs={"slug": self.slug})


class Guide(models.Model):
    """Buying guides and how-to articles."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, validators=[not_only_digits], help_text="Page address: /guides/<slug>/")
    summary = models.TextField(
        help_text="A direct 1–3 sentence answer. Shown at the top of the guide and in search results."
    )
    body = models.TextField(help_text=BODY_HELP)
    cover_image = models.ImageField(upload_to="guides/", blank=True)
    author_name = models.CharField(
        max_length=120, blank=True, help_text="Real name of the person who wrote or checked this guide (optional)."
    )
    related_category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Tiles from this category are suggested at the end of the guide.",
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:guide_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

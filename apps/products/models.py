"""
Product models for the Suwasthick Tiles catalog.
"""
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify

from apps.core.models import Category

from .sizes import display_size


class Product(models.Model):
    MATERIAL_CHOICES = [
        ("ceramic", "Ceramic"),
        ("porcelain", "Porcelain"),
        ("marble", "Marble"),
        ("granite", "Granite"),
        ("slate", "Slate"),
        ("glass", "Glass"),
        ("travertine", "Travertine"),
        ("limestone", "Limestone"),
        ("mosaic", "Mosaic"),
        ("terracotta", "Terracotta"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES, default="ceramic")
    size = models.CharField(
        max_length=50,
        help_text='Free text — type any size, e.g. "600x1200mm", "60x60cm", "2x2 ft"',
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Primary category (shown as the main badge).",
    )
    additional_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="extra_products",
        help_text="Other categories this tile should ALSO appear under (e.g. a floor tile also listed in Bathroom).",
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def slug(self):
        """URL slug from the name: 'MAC VERDE-CV' -> 'mac-verde-cv'."""
        return slugify(self.name) or "product"

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.pk, "slug": self.slug})

    @property
    def clear_size(self):
        """Normalised size like '60×60 cm', or None when the size is unclear (e.g. '4/2')."""
        return display_size(self.size)

    @property
    def kind(self):
        """'floor tile', 'bathroom tile', 'sanitaryware' or just 'tile'."""
        return self.category.singular_name.lower() if self.category else "tile"

    @property
    def descriptive_name(self):
        """Readable description for alt text, e.g. 'Myglamm Grey 60×60 cm porcelain floor tile'."""
        parts = [self.name]
        if self.clear_size:
            parts.append(self.clear_size)
        parts.append(self.get_material_display().lower())
        parts.append(self.kind)
        return " ".join(parts)

    @property
    def all_categories(self):
        """Primary category first, then any additional ones (deduped)."""
        cats = []
        if self.category:
            cats.append(self.category)
        for c in self.additional_categories.all():
            if c not in cats:
                cats.append(c)
        return cats


class ProductImage(models.Model):
    """Extra gallery photos for a product — designs and fitted-room shots."""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="gallery"
    )
    image = models.ImageField(upload_to="products/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.product.name}"


# ── File cleanup: remove image files from disk on delete / replace ──
def _delete_file(filefield):
    if filefield and filefield.name:
        filefield.delete(save=False)


@receiver(post_delete, sender=Product)
def _product_deleted(sender, instance, **kwargs):
    _delete_file(instance.image)


@receiver(post_delete, sender=ProductImage)
def _productimage_deleted(sender, instance, **kwargs):
    _delete_file(instance.image)


@receiver(pre_save, sender=Product)
def _product_image_replaced(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Product.objects.get(pk=instance.pk).image
    except Product.DoesNotExist:
        return
    if old and old.name and old.name != instance.image.name:
        _delete_file(old)


@receiver(pre_save, sender=ProductImage)
def _productimage_replaced(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = ProductImage.objects.get(pk=instance.pk).image
    except ProductImage.DoesNotExist:
        return
    if old and old.name and old.name != instance.image.name:
        _delete_file(old)


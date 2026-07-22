"""
Core app models - site-wide models like banners, categories etc.
"""
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS/emoji icon")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to="banners/", null=True, blank=True)
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


# ── File cleanup: remove image files from disk on delete / replace ──
def _delete_file(filefield):
    if filefield and filefield.name:
        filefield.delete(save=False)


@receiver(post_delete, sender=Category)
def _category_deleted(sender, instance, **kwargs):
    _delete_file(instance.image)


@receiver(post_delete, sender=Banner)
def _banner_deleted(sender, instance, **kwargs):
    _delete_file(instance.image)


@receiver(pre_save, sender=Category)
def _category_image_replaced(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Category.objects.get(pk=instance.pk).image
    except Category.DoesNotExist:
        return
    if old and old.name and old.name != instance.image.name:
        _delete_file(old)


@receiver(pre_save, sender=Banner)
def _banner_image_replaced(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Banner.objects.get(pk=instance.pk).image
    except Banner.DoesNotExist:
        return
    if old and old.name and old.name != instance.image.name:
        _delete_file(old)

"""
Make WebP renditions whenever an image is uploaded or changed.
"""
from django.db.models.signals import post_save

from .images import generate_renditions

# model label -> image fields that get renditions
IMAGE_FIELDS = {
    "products.Product": ("image",),
    "products.ProductImage": ("image",),
    "core.Category": ("image",),
    "core.Banner": ("image",),
    "content.Guide": ("cover_image",),
}


def make_renditions(sender, instance, raw=False, **kwargs):
    if raw:  # loading fixtures
        return
    for field in IMAGE_FIELDS.get(sender._meta.label, ()):
        generate_renditions(getattr(instance, field))


def connect():
    for label in IMAGE_FIELDS:
        post_save.connect(make_renditions, sender=label, dispatch_uid=f"renditions-{label}")

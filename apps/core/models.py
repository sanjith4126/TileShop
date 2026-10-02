"""
Core app models - site-wide models like banners, categories etc.
"""
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.urls import reverse

# Category pages live at /products/<slug>/ and product pages at /products/<id>/...,
# so a slug made only of digits would collide with product URLs.
not_only_digits = RegexValidator(
    regex=r"^\d+$",
    inverse_match=True,
    message="The slug can't be only numbers. Add a word, e.g. 'floor-tiles'.",
)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(
        unique=True,
        validators=[not_only_digits],
        help_text="Used in the page address: /products/<slug>/. Changing it changes the URL.",
    )
    description = models.TextField(
        blank=True,
        help_text="Short introduction shown at the top of the category page and used in search results.",
    )
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS/emoji icon")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category_detail", kwargs={"category_slug": self.slug})

    @property
    def singular_name(self):
        """'Floor Tiles' -> 'Floor Tile' (for titles like '... Porcelain Floor Tile')."""
        name = self.name.strip()
        return name[:-1] if name.lower().endswith("tiles") else name


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


class Inquiry(models.Model):
    """A quote / contact request submitted through the inquiry form."""

    REFERRER_CHOICES = [
        ("engineer", "Civil Engineer"),
        ("mason", "Mason"),
        ("layer", "Layer (Tile Fixer)"),
        ("architect", "Architect"),
        ("others", "Others"),
    ]
    PROJECT_TYPE_CHOICES = [
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("hospitality", "Hospitality / Hotel"),
        ("restoration", "Heritage Restoration"),
        ("outdoor", "Outdoor / Landscaping"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("quoted", "Quote sent"),
        ("closed", "Closed"),
    ]

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField("address / location", max_length=255, blank=True)
    referrer_type = models.CharField(
        "referred by", max_length=20, choices=REFERRER_CHOICES, blank=True
    )
    referrer_name = models.CharField("professional's name", max_length=200, blank=True)
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        help_text="The tile the customer was looking at when they asked for a quote.",
    )
    tile_interest = models.CharField("tiles interested in", max_length=255, blank=True)
    area_sqft = models.PositiveIntegerField("area required (sq.ft)", null=True, blank=True)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "quote request"
        verbose_name_plural = "quote requests"

    def __str__(self):
        return f"Quote request from {self.full_name}"


class BusinessInfo(models.Model):
    """
    The shop's contact details, shown in the footer, About and contact pages.
    There is only one record. Details are published to Google (structured
    data) and made clickable only after "details confirmed" is ticked.
    """

    address = models.CharField(
        "address (as shown on the site)", max_length=255, blank=True,
        help_text="E.g. 'Opp. Kalyana Mandabam, Bhavani, Erode Dt, Tamil Nadu'.",
    )
    street_address = models.CharField(
        max_length=255, blank=True, help_text="Street / landmark line for Google, e.g. 'Opp. Kalyana Mandabam'."
    )
    locality = models.CharField("town / city", max_length=100, blank=True)
    region = models.CharField("state", max_length=100, blank=True)
    postal_code = models.CharField("PIN code", max_length=10, blank=True)
    country = models.CharField(max_length=2, default="IN", help_text="Two-letter country code.")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    maps_url = models.URLField(
        "Google Maps link", blank=True, help_text="Used for the 'Get directions' button."
    )
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(
        "WhatsApp number", max_length=20, blank=True,
        help_text="With country code, digits only, e.g. 919876543210.",
    )
    email = models.EmailField(blank=True)
    opening_hours = models.CharField(
        "opening hours (as shown on the site)", max_length=120, blank=True,
        help_text="E.g. 'Mon–Sat, 9 AM to 7 PM'.",
    )
    opening_hours_spec = models.CharField(
        "opening hours for Google", max_length=120, blank=True,
        help_text="Schema.org format, e.g. 'Mo-Sa 09:00-19:00'. Several ranges: separate with commas.",
    )
    service_areas = models.CharField(
        max_length=255, blank=True, help_text="Towns/districts you deliver to, separated by commas."
    )
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    google_business_url = models.URLField("Google Business Profile link", blank=True)
    logo = models.ImageField(upload_to="brand/", blank=True)
    share_image = models.ImageField(
        upload_to="brand/", blank=True,
        help_text="1200×630 image used in link previews (WhatsApp, Facebook) when a page has no image of its own.",
    )
    details_confirmed = models.BooleanField(
        default=False,
        help_text=(
            "Tick once the address, phone, email and hours above are correct. Only then are they "
            "published to Google (structured data) and the phone/email made clickable."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "business info"
        verbose_name_plural = "business info"

    def __str__(self):
        return "Business info"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def phone_href(self):
        digits = "".join(ch for ch in self.phone if ch.isdigit() or ch == "+")
        return f"tel:{digits}" if digits else ""

    @property
    def whatsapp_href(self):
        digits = "".join(ch for ch in self.whatsapp if ch.isdigit())
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def social_links(self):
        links = [
            ("Facebook", self.facebook_url),
            ("Instagram", self.instagram_url),
            ("YouTube", self.youtube_url),
            ("Google", self.google_business_url),
        ]
        return [(label, url) for label, url in links if url]


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


@receiver(pre_save, sender=BusinessInfo)
def _business_images_replaced(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = BusinessInfo.objects.filter(pk=instance.pk).first()
    if not old:
        return
    for field in ("logo", "share_image"):
        old_file, new_file = getattr(old, field), getattr(instance, field)
        if old_file and old_file.name and old_file.name != new_file.name:
            _delete_file(old_file)


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

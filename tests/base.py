"""
Shared test fixtures: a small catalog with real (tiny) images in a temporary
MEDIA_ROOT, so tests never touch the real media folder.
"""
import atexit
import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.core.models import Category
from apps.products.models import Product

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="tileshop-test-media-")
atexit.register(shutil.rmtree, TEMP_MEDIA_ROOT, ignore_errors=True)


def image_bytes(size=(64, 48), color=(180, 160, 140), fmt="PNG"):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, fmt)
    return buf.getvalue()


def image_upload(name="tile.png", size=(64, 48), fmt="PNG"):
    content_type = "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"
    return SimpleUploadedFile(name, image_bytes(size=size, fmt=fmt), content_type=content_type)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ShopTestCase(TestCase):
    """Categories: floor (2 products), bathroom (1), wall (empty). Plus edge-case products."""

    @classmethod
    def setUpTestData(cls):
        cls.floor = Category.objects.create(
            name="Floor Tiles", slug="floor-tiles", description="Tiles designed for flooring applications"
        )
        cls.bathroom = Category.objects.create(
            name="Bathroom Tiles", slug="bathroom-tiles", description="Specialized tiles for bathroom use"
        )
        cls.wall = Category.objects.create(
            name="Wall Tiles", slug="wall-tiles", description="Tiles designed for wall applications"
        )
        cls.product = Product.objects.create(
            name="Myglamm Grey",
            description="Sophisticated grey floor tile with natural texture",
            price=Decimal("520.00"),
            material="porcelain",
            size="60x60cm",
            category=cls.floor,
            stock=150,
            is_featured=True,
            image=image_upload("myglamm-grey.png"),
        )
        cls.unclear_size = Product.objects.create(
            name="ALTROZ GREY",
            description="Altroz Grey – a blend of modern elegance and timeless style",
            price=Decimal("54.00"),
            material="ceramic",
            size="4/2",
            category=cls.floor,
            stock=100,
            image=image_upload("altroz-grey.png"),
        )
        cls.bath_product = Product.objects.create(
            name="JUNGLE LUSH",
            description="carving matt",
            price=Decimal("65.00"),
            material="ceramic",
            size="1200X600mm",
            category=cls.bathroom,
            stock=100,
            image=image_upload("jungle-lush.png"),
        )
        cls.no_category = Product.objects.create(
            name="LUXE GREY",
            description="Luxe Grey – a luxurious grey finish",
            price=Decimal("54.00"),
            material="ceramic",
            size="4/2",
            category=None,
            stock=100,
        )
        cls.out_of_stock = Product.objects.create(
            name="SCONE YELLOW",
            description="A vibrant yellow surface",
            price=Decimal("54.00"),
            material="ceramic",
            size="",
            category=cls.floor,
            stock=0,
        )
        cls.inactive = Product.objects.create(
            name="Discontinued Tile",
            description="No longer sold",
            price=Decimal("99.00"),
            category=cls.floor,
            is_active=False,
        )

    def setUp(self):
        cache.clear()

    def add_to_cart(self, product, quantity=1):
        return self.client.post(f"/cart/add/{product.pk}/", {"quantity": quantity})

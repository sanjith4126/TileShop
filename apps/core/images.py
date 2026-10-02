"""
Responsive image renditions.

Every uploaded image gets WebP copies at up to three widths (never upscaled),
stored as  renditions/<original path without extension>-<width>w.webp
The original file is kept untouched for full-size viewing.

Renditions are created when an image is saved (see signals in apps.py) and
for existing images with:  python manage.py build_image_renditions
"""
import logging
import posixpath
import re
from io import BytesIO

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

RENDITION_WIDTHS = (400, 800, 1200)
RENDITIONS_DIR = "renditions"
WEBP_QUALITY = 82
CACHE_SECONDS = 3600


def rendition_stem(name):
    return f"{RENDITIONS_DIR}/{name.rsplit('.', 1)[0]}"


def rendition_name(name, width):
    return f"{rendition_stem(name)}-{width}w.webp"


def _cache_key(name):
    return "renditions:" + re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def target_widths(original_width):
    """Widths to generate for an image: never wider than the original."""
    return sorted({min(w, original_width) for w in RENDITION_WIDTHS})


def generate_renditions(field_file, force=False, storage=None):
    """Create the WebP renditions for one image. Returns the names written."""
    if not field_file or not getattr(field_file, "name", ""):
        return []
    storage = storage or field_file.storage
    name = field_file.name
    try:
        with storage.open(name, "rb") as fh:
            img = Image.open(fh)
            img.load()
    except Exception:
        logger.warning("Could not open %s to make renditions", name, exc_info=True)
        return []

    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode not in ("RGB", "RGBA"):
        has_alpha = img.mode in ("LA", "P") and ("transparency" in img.info or img.mode == "LA")
        img = img.convert("RGBA" if has_alpha else "RGB")

    try:
        original_time = storage.get_modified_time(name)
    except (NotImplementedError, OSError):
        original_time = None

    written = []
    for width in target_widths(img.width):
        target = rendition_name(name, width)
        if storage.exists(target):
            stale = False
            if original_time is not None:
                try:
                    stale = storage.get_modified_time(target) < original_time
                except (NotImplementedError, OSError):
                    stale = True
            if not (force or stale):
                continue
            storage.delete(target)
        copy = img.copy()
        copy.thumbnail((width, 100000), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        copy.save(buffer, "WEBP", quality=WEBP_QUALITY, method=6)
        storage.save(target, ContentFile(buffer.getvalue()))
        written.append(target)
    cache.delete(_cache_key(name))
    return written


def delete_renditions(name, storage=None):
    """Remove every rendition of ``name`` (called when an image is deleted or replaced)."""
    if not name:
        return
    storage = storage or default_storage
    for width, rendition in renditions_for(name, storage=storage, use_cache=False):
        try:
            storage.delete(rendition)
        except Exception:
            logger.warning("Could not delete rendition %s", rendition, exc_info=True)
    cache.delete(_cache_key(name))


def renditions_for(name, storage=None, use_cache=True):
    """[(width, rendition_name), ...] that exist for ``name``, smallest first."""
    if not name:
        return []
    key = _cache_key(name)
    if use_cache:
        cached = cache.get(key)
        if cached is not None:
            return cached
    storage = storage or default_storage
    directory, prefix = posixpath.split(rendition_stem(name))
    pattern = re.compile(re.escape(prefix) + r"-(\d+)w\.webp$")
    try:
        _, files = storage.listdir(directory)
    except (FileNotFoundError, NotADirectoryError, OSError):
        files = []
    found = sorted(
        (int(m.group(1)), posixpath.join(directory, f)) for f in files if (m := pattern.match(f))
    )
    cache.set(key, found, CACHE_SECONDS)
    return found

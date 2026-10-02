"""
List files in MEDIA_ROOT that no image/file field in the database points to.

This command only reports. It never deletes anything — review the list and
delete files yourself if you're sure they aren't needed.

    python manage.py find_unused_media
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models

# Generated copies (WebP renditions) live here and belong to their originals.
RENDITIONS_DIR = "renditions/"


def referenced_media_files():
    """Paths (relative to MEDIA_ROOT, forward slashes) of every file a model field uses."""
    referenced = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if not isinstance(field, models.FileField):
                continue
            values = (
                model._default_manager.exclude(**{field.name: ""})
                .exclude(**{f"{field.name}__isnull": True})
                .values_list(field.name, flat=True)
            )
            referenced.update(str(v).replace("\\", "/") for v in values.iterator())
    return referenced


def rendition_belongs_to(rel_path, referenced):
    """True if ``rel_path`` is a rendition of a referenced original (renditions/<stem>-<w>w.webp)."""
    stem = rel_path[len(RENDITIONS_DIR):].rsplit("-", 1)[0]
    return any(name.rsplit(".", 1)[0] == stem for name in referenced)


class Command(BaseCommand):
    help = "List media files that nothing in the database uses (read-only; never deletes)."

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stdout.write(f"MEDIA_ROOT does not exist: {media_root}")
            return

        referenced = referenced_media_files()
        unused, total_bytes = [], 0
        for path in sorted(media_root.rglob("*")):
            if not path.is_file() or path.name == ".gitkeep":
                continue
            rel = path.relative_to(media_root).as_posix()
            if rel in referenced:
                continue
            if rel.startswith(RENDITIONS_DIR) and rendition_belongs_to(rel, referenced):
                continue
            size = path.stat().st_size
            unused.append((rel, size))
            total_bytes += size

        missing = sorted(name for name in referenced if not (media_root / name).exists())

        if unused:
            self.stdout.write(self.style.WARNING(f"{len(unused)} unused file(s), {total_bytes / 1024:.0f} KB:"))
            for rel, size in unused:
                self.stdout.write(f"  {rel}  ({size / 1024:.0f} KB)")
            self.stdout.write("Nothing was deleted. Remove these files manually if they aren't needed.")
        else:
            self.stdout.write(self.style.SUCCESS("No unused media files."))

        if missing:
            self.stdout.write(self.style.ERROR(f"{len(missing)} file(s) referenced in the database but missing on disk:"))
            for name in missing:
                self.stdout.write(f"  {name}")

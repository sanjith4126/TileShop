"""
Create WebP renditions (400/800/1200 px wide, never upscaled) for every
uploaded image. Safe to run repeatedly; existing renditions are skipped
unless --force is given. Run after deploying or after bulk-uploading images.

    python manage.py build_image_renditions
"""
from django.apps import apps
from django.core.management.base import BaseCommand

from apps.core.images import generate_renditions
from apps.core.signals import IMAGE_FIELDS


class Command(BaseCommand):
    help = "Create WebP renditions for all uploaded images."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Rebuild renditions that already exist.")

    def handle(self, *args, **options):
        created = 0
        for label, fields in IMAGE_FIELDS.items():
            model = apps.get_model(label)
            for obj in model._default_manager.all().iterator():
                for field in fields:
                    file = getattr(obj, field)
                    if file and file.name:
                        written = generate_renditions(file, force=options["force"])
                        created += len(written)
                        for name in written:
                            self.stdout.write(f"  {name}")
        self.stdout.write(self.style.SUCCESS(f"Created {created} rendition(s)."))

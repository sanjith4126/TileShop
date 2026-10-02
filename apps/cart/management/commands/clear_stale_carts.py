"""
Delete carts nobody can reach any more: their session has expired or been
removed. Bots and one-time visitors leave these behind. Run it after
clearsessions, for example as a daily scheduled task:

    python manage.py clearsessions && python manage.py clear_stale_carts

Orders are separate records and are never touched. --dry-run only counts.
"""
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.cart.models import Cart

DB_SESSION_ENGINES = ("django.contrib.sessions.backends.db", "django.contrib.sessions.backends.cached_db")


class Command(BaseCommand):
    help = "Delete carts whose session has expired or no longer exists. Orders are not affected."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only report how many carts would be deleted.")

    def handle(self, *args, **options):
        if settings.SESSION_ENGINE not in DB_SESSION_ENGINES:
            raise CommandError("Carts are matched to sessions stored in the database; "
                               f"SESSION_ENGINE is {settings.SESSION_ENGINE}.")
        live_sessions = Session.objects.filter(expire_date__gt=timezone.now()).values("session_key")
        stale = Cart.objects.exclude(session_id__in=live_sessions)
        count = stale.count()
        if options["dry_run"]:
            self.stdout.write(f"{count} stale cart(s) would be deleted.")
            return
        stale.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} stale cart(s)."))

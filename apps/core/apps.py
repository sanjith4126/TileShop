from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from apps.core.context_processors import clear_nav_cache

        # Navigation data is cached; refresh it whenever categories or products change.
        for model in ("core.Category", "products.Product"):
            post_save.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-save-{model}")
            post_delete.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-delete-{model}")

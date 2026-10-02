from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content"
    label = "content"
    verbose_name = "Guides and pages"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from apps.core.context_processors import clear_nav_cache

        # The footer lists published pages and links to guides; refresh it on changes.
        for model in ("content.Page", "content.Guide"):
            post_save.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-save-{model}")
            post_delete.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-delete-{model}")

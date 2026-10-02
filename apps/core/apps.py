from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        from django.db.models.signals import m2m_changed, post_delete, post_save

        from apps.core.context_processors import clear_business_cache, clear_nav_cache
        from apps.products.models import Product

        # Navigation data is cached; refresh it whenever categories or products change.
        for model in ("core.Category", "products.Product"):
            post_save.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-save-{model}")
            post_delete.connect(clear_nav_cache, sender=model, dispatch_uid=f"nav-cache-delete-{model}")
        m2m_changed.connect(
            clear_nav_cache,
            sender=Product.additional_categories.through,
            dispatch_uid="nav-cache-m2m",
        )
        post_save.connect(clear_business_cache, sender="core.BusinessInfo", dispatch_uid="business-cache-save")

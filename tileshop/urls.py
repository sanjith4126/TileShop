"""
URL configuration for the Suwasthick Tiles website.
"""

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.core import views as core_views
from apps.core.sitemaps import SITEMAPS

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("favicon.ico", core_views.favicon, {"name": "favicon.ico"}, name="favicon"),
    path("apple-touch-icon.png", core_views.favicon, {"name": "apple-touch-icon.png"}),
    path("", include("apps.core.urls")),
    path("products/", include("apps.products.urls")),
    path("cart/", include("apps.cart.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("orders/", include("apps.orders.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Suwasthick Tiles Admin"
admin.site.site_title = "Suwasthick Tiles"
admin.site.index_title = "Store Administration"

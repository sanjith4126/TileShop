"""
Products app URL patterns.

    /products/                     all products
    /products/<id>/                old product URL -> 301 to the one below
    /products/<id>/<slug>/         product page
    /products/<category-slug>/     category page
"""
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("<int:pk>/", views.product_legacy_redirect, name="product_legacy"),
    path("<int:pk>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("<slug:category_slug>/", views.category_detail, name="category_detail"),
]

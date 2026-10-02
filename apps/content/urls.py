"""
Content URL patterns: /guides/, /guides/<slug>/, /policies/<slug>/
"""
from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("guides/", views.guide_list, name="guide_list"),
    path("guides/<slug:slug>/", views.guide_detail, name="guide_detail"),
    path("policies/<slug:slug>/", views.page_detail, name="page_detail"),
]

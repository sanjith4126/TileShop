"""
Core app URL patterns.
"""
from django.urls import path
from apps.products import views as product_views

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("room-visualizer/", views.room_visualizer, name="room_visualizer"),
    path("room-visualizer/generate/", views.ai_visualize, name="ai_visualize"),
    path("inquiry/", views.inquiry, name="inquiry"),
    path("tile-calculator/", views.tile_calculator, name="tile_calculator"),
    path("search/", product_views.search, name="search"),
]

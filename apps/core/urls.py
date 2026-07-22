"""
Core app URL patterns.
"""
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("room-visualizer/", views.room_visualizer, name="room_visualizer"),
    path("room-visualizer/generate/", views.ai_visualize, name="ai_visualize"),
    path("inquiry/", views.inquiry, name="inquiry"),
]

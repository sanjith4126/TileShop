"""
Accounts app views - registration, login, logout, and dashboard.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from apps.orders.models import Order


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get("next", "accounts:dashboard")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome to TileShop Premium.")
            return redirect("accounts:dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")


@login_required
def dashboard_view(request):
    """User dashboard - order history and account info."""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    context = {
        "orders": orders,
    }
    return render(request, "accounts/dashboard.html", context)


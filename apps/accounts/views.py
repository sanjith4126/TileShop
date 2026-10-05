"""
Accounts app views - registration, login, logout, and dashboard.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.cart.models import Cart
from apps.core.seo import NOINDEX_FOLLOW, NOINDEX_NOFOLLOW, page_meta
from apps.orders.models import Order


def _safe_next_url(request):
    """The ?next= target if it points to this site, otherwise the dashboard."""
    candidate = request.POST.get("next") or request.GET.get("next") or ""
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return reverse("accounts:dashboard")


def _log_in(request, user):
    """Log in without losing the cart. login() moves the session to a new key,
    and carts are stored against the session key."""
    old_key = request.session.session_key
    login(request, user)
    new_key = request.session.session_key
    if old_key and new_key and old_key != new_key:
        Cart.objects.filter(session_id=old_key).update(session_id=new_key)


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            _log_in(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(_safe_next_url(request))
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)

    context = {
        "form": form,
        "next": request.POST.get("next") or request.GET.get("next", ""),
        "seo": page_meta(request, "Sign In", robots=NOINDEX_FOLLOW),
    }
    return render(request, "accounts/login.html", context)


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            _log_in(request, user)
            messages.success(request, "Account created! Welcome to Suwasthik Tiles.")
            return redirect("accounts:dashboard")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form, "seo": page_meta(request, "Create Account", robots=NOINDEX_FOLLOW)})


def logout_view(request):
    """Log out on POST only, so other sites can't log visitors out with a link."""
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")


@login_required
def dashboard_view(request):
    """User dashboard - order history and account info."""
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    context = {
        "orders": orders,
        "seo": page_meta(request, "My Dashboard", robots=NOINDEX_NOFOLLOW),
    }
    return render(request, "accounts/dashboard.html", context)

"""
Core app views — homepage, about, room visualizer, inquiry (quote requests).
"""
import base64
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_GET, require_POST

from apps.core.models import Banner, Category, Inquiry
from apps.products.models import Product

from . import ai
from .context_processors import DEFAULT_DESCRIPTION, DEFAULT_TITLE
from .forms import InquiryForm
from .notifications import notify_shop
from .seo import absolute_url, page_meta
from .utils import parse_positive_int

logger = logging.getLogger(__name__)


def home(request):
    """Homepage view."""
    featured_products = (
        Product.objects.filter(is_featured=True, is_active=True).select_related("category")[:8]
    )
    categories = Category.objects.all()
    banners = Banner.objects.filter(is_active=True)

    context = {
        "featured_products": featured_products,
        "categories": categories,
        "banners": banners,
        "seo": page_meta(request, DEFAULT_TITLE, DEFAULT_DESCRIPTION, full_title=True),
    }
    return render(request, "home.html", context)


def about(request):
    """About / Our Story page."""
    context = {
        "seo": page_meta(
            request,
            "About Us – Our Showroom in Bhavani",
            "Suwasthick Tiles is a tile and sanitaryware showroom opposite Kalyana Mandabam in Bhavani, "
            "Erode district, Tamil Nadu. Learn about our range, our showroom and how to order.",
        ),
    }
    return render(request, "about.html", context)


@require_GET
def robots_txt(request):
    """robots.txt: keep crawlers out of carts and orders; point them to the sitemap."""
    lines = [
        "User-agent: *",
        "Disallow: /cart/",
        "Disallow: /orders/",
        "Disallow: /room-visualizer/generate/",
        "",
        f"Sitemap: {absolute_url(reverse('sitemap'), request)}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


@require_GET
def favicon(request, name="favicon.ico"):
    """Browsers ask for /favicon.ico and /apple-touch-icon.png at the site root."""
    target = {"favicon.ico": "favicon.ico", "apple-touch-icon.png": "icons/apple-touch-icon.png"}[name]
    return redirect(static(target))


def room_visualizer(request):
    """Room Visualizer page — upload a photo, pick a tile, let the AI fit it."""
    products = (
        Product.objects.filter(is_active=True, image__isnull=False)
        .exclude(image="")
        .exclude(category__name="Sanitaryware")
        .select_related("category")[:24]
    )
    selected_product = None
    product_pk = parse_positive_int(request.GET.get("product"))
    if product_pk:
        selected_product = (
            Product.objects.filter(pk=product_pk, is_active=True).select_related("category").first()
        )

    context = {
        "products": products,
        "selected_product": selected_product,
        "ai_enabled": bool(settings.GEMINI_API_KEY),
        "seo": page_meta(
            request,
            "AI Room Visualizer – See Tiles in Your Room",
            "Upload a photo of your room, choose a tile from the Suwasthick Tiles collection and see it "
            "fitted on your floor or wall with our AI room visualizer.",
        ),
    }
    return render(request, "room_visualizer.html", context)


def inquiry(request):
    """Quote / inquiry request form. Every valid submission is saved."""
    raw_product = request.POST.get("product_id") if request.method == "POST" else request.GET.get("product")
    product = None
    product_pk = parse_positive_int(raw_product)
    if product_pk:
        product = Product.objects.filter(pk=product_pk, is_active=True).select_related("category").first()

    if request.method == "POST":
        form = InquiryForm(request.POST)
        if form.is_valid():
            quote_request = form.save(commit=False)
            quote_request.product = product
            if product and not quote_request.tile_interest:
                quote_request.tile_interest = product.name
            quote_request.save()
            _notify_new_inquiry(request, quote_request)
            # Show the confirmation once, on the redirected page.
            request.session["inquiry_submitted"] = True
            return redirect("core:inquiry")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"full_name": request.user.get_full_name(), "email": request.user.email}
        if request.GET.get("referrer_type") in dict(Inquiry.REFERRER_CHOICES):
            initial["referrer_type"] = request.GET["referrer_type"]
        form = InquiryForm(initial=initial)

    context = {
        "form": form,
        "product": product,
        "success": request.session.pop("inquiry_submitted", False),
        "seo": page_meta(
            request,
            "Request a Quote – Contact Us",
            "Ask Suwasthick Tiles in Bhavani for a quote on floor, wall, bathroom, kitchen and parking tiles "
            "or sanitaryware. Tell us about your project and we'll get back to you.",
        ),
    }
    return render(request, "inquiry/inquiry_form.html", context)


def _notify_new_inquiry(request, quote_request):
    lines = [
        f"Name: {quote_request.full_name}",
        f"Phone: {quote_request.phone}",
        f"Email: {quote_request.email}",
    ]
    optional = [
        ("Location", quote_request.address),
        ("Tiles", quote_request.tile_interest),
        ("Area (sq.ft)", quote_request.area_sqft),
        ("Project type", quote_request.get_project_type_display() if quote_request.project_type else ""),
        ("Referred by", " ".join(filter(None, [
            quote_request.get_referrer_type_display() if quote_request.referrer_type else "",
            quote_request.referrer_name,
        ]))),
        ("Message", quote_request.message),
    ]
    lines += [f"{label}: {value}" for label, value in optional if value]
    try:
        lines.append("")
        lines.append("Open in admin: " + request.build_absolute_uri(
            reverse("admin:core_inquiry_change", args=[quote_request.pk])
        ))
    except NoReverseMatch:
        pass
    notify_shop(f"New quote request from {quote_request.full_name}", "\n".join(lines))


# ── AI Room Visualizer (Gemini image editing) ──────────────────────

def _client_ip(request):
    # PythonAnywhere's proxy puts the visitor's address in X-Real-IP.
    return (request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "unknown").strip()


def _recent_visualizer_uses(request, now):
    window = settings.VISUALIZER_RATE_WINDOW
    return [t for t in request.session.get("visualizer_uses", []) if now - t < window]


def _visualizer_rate_limited(request):
    """True if this visitor (session, or IP address) has used up the allowance."""
    limit = settings.VISUALIZER_RATE_LIMIT
    if limit <= 0:
        return False
    if len(_recent_visualizer_uses(request, time.time())) >= limit:
        return True
    # Mobile networks often share one IP address between many people, so the
    # per-IP allowance is more generous than the per-visitor one.
    return cache.get(f"visualizer:ip:{_client_ip(request)}", 0) >= limit * 4


def _record_visualizer_use(request):
    now = time.time()
    uses = _recent_visualizer_uses(request, now)
    uses.append(now)
    request.session["visualizer_uses"] = uses
    key = f"visualizer:ip:{_client_ip(request)}"
    if not cache.add(key, 1, settings.VISUALIZER_RATE_WINDOW):
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, settings.VISUALIZER_RATE_WINDOW)


def _error(message, status):
    return JsonResponse({"error": message}, status=status)


@require_POST
def ai_visualize(request):
    """
    Take an uploaded room photo + a selected tile and use Gemini to re-render
    the room's floor/wall with that tile. Returns JSON with a base64 data-URL.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return _error("The AI visualizer isn't available right now. Request a quote and we'll help you choose.", 503)

    if _visualizer_rate_limited(request):
        return _error("You've reached the limit for AI visualizations for now. Please try again later.", 429)

    photo = request.FILES.get("photo")
    product_id = parse_positive_int(request.POST.get("product_id"))
    if not photo:
        return _error("Please upload a room photo first.", 400)
    if not product_id:
        return _error("Please select a tile first.", 400)
    if photo.size > settings.VISUALIZER_MAX_UPLOAD_BYTES:
        limit_mb = settings.VISUALIZER_MAX_UPLOAD_BYTES // (1024 * 1024)
        return _error(f"That photo is too large. Please upload an image under {limit_mb} MB.", 413)

    product = Product.objects.filter(pk=product_id, is_active=True).select_related("category").first()
    if not product or not product.image:
        return _error("Please select a tile that has a photo.", 400)

    try:
        room_bytes, room_mime = ai.prepare_image(photo, settings.VISUALIZER_MAX_IMAGE_SIDE)
    except ai.InvalidImage:
        return _error("Please upload a JPG, PNG or WebP photo of your room.", 400)

    try:
        with product.image.open("rb") as fh:
            tile_bytes, tile_mime = ai.prepare_image(fh, 1024)
    except (OSError, ai.InvalidImage):
        logger.exception("Could not read the tile image for product %s", product.pk)
        return _error("We couldn't prepare this tile. Please choose another tile.", 500)

    surface = ai.surface_for_category(product.category.name if product.category else "")
    _record_visualizer_use(request)

    try:
        image_bytes, mime = ai.render_room_with_tile(
            api_key, ai.build_prompt(surface), room_bytes, room_mime, tile_bytes, tile_mime
        )
    except ai.VisualizerBusy:
        logger.warning("Gemini refused a visualizer request (quota, rate or billing limit).", exc_info=True)
        return _error("The AI visualizer is busy right now. Please try again in a few minutes.", 503)
    except ai.VisualizerError:
        logger.exception("Gemini visualizer request failed")
        return _error("The AI visualizer couldn't process this photo. Please try again or use a clearer photo.", 502)

    if not image_bytes:
        return _error("The AI didn't return an image. Try a clearer, well-lit room photo.", 502)

    b64 = base64.b64encode(image_bytes).decode("ascii")
    return JsonResponse({"image": f"data:{mime};base64,{b64}"})

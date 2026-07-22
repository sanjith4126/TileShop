"""
Core app views — homepage, about, room visualizer, inquiry.
"""
import os
import json
import base64
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.products.models import Product
from apps.core.models import Category, Banner


ROOM_TEMPLATES = [
    {
        "key": "bathroom",
        "name": "Master Bathroom",
        "description": "Wall & floor tiles",
        "image": "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=1200&q=80",
    },
    {
        "key": "kitchen",
        "name": "Gourmet Kitchen",
        "description": "Floor & backsplash",
        "image": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1200&q=80",
    },
    {
        "key": "living",
        "name": "Living Room",
        "description": "Large format floors",
        "image": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1200&q=80",
    },
    {
        "key": "bedroom",
        "name": "Bedroom",
        "description": "Soft textured tiles",
        "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=1200&q=80",
    },
    {
        "key": "outdoor",
        "name": "Outdoor Patio",
        "description": "Non-slip outdoor tiles",
        "image": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=1200&q=80",
    },
    {
        "key": "commercial",
        "name": "Commercial / Office",
        "description": "High-traffic surfaces",
        "image": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&q=80",
    },
]


def home(request):
    """Homepage view."""
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    categories = Category.objects.all()
    banners = Banner.objects.filter(is_active=True)

    context = {
        "featured_products": featured_products,
        "categories": categories,
        "banners": banners,
        "material_choices": Product.MATERIAL_CHOICES,
    }
    return render(request, "home.html", context)


def about(request):
    """About / Our Story page."""
    return render(request, "about.html", {})


def room_visualizer(request):
    """Room Visualizer page — upload a photo, mark the surface, fit tiles."""
    products = (
        Product.objects.filter(is_active=True, image__isnull=False)
        .exclude(image="")
        .exclude(category__name="Sanitaryware")[:24]
    )
    selected_product = None
    product_pk = request.GET.get("product")
    if product_pk:
        try:
            selected_product = Product.objects.get(pk=product_pk, is_active=True)
        except Product.DoesNotExist:
            pass

    context = {
        "products": products,
        "selected_product": selected_product,
    }
    return render(request, "room_visualizer.html", context)


def inquiry(request):
    """Quote / Inquiry request form."""
    product = None
    product_pk = request.GET.get("product")
    if product_pk:
        try:
            product = Product.objects.get(pk=product_pk, is_active=True)
        except Product.DoesNotExist:
            pass

    success = False
    if request.method == "POST":
        # Collect form data — store as a simple log for now
        # In production, save to Inquiry model or send email
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        if full_name and email and phone:
            success = True
            messages.success(request, f"Thank you {full_name}! We will contact you at {email} within 24 hours.")
            # Reset to GET after successful submission
            return redirect(request.path + "?submitted=1")

    context = {
        "product": product,
        "success": request.GET.get("submitted") == "1",
    }
    return render(request, "inquiry/inquiry_form.html", context)


# ── AI Room Visualizer (Gemini image editing) ──────────────────────
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"


def _surface_for_category(name):
    """Decide whether a category's tiles go on the floor or the wall."""
    n = (name or "").lower()
    if "wall" in n or "bathroom" in n:
        return "wall"
    return "floor"


@require_POST
def ai_visualize(request):
    """
    Take an uploaded room photo + a selected tile and use Gemini to
    re-render the room's floor/wall with that tile. Returns JSON with a
    base64 data-URL of the result image.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return JsonResponse(
            {"error": "AI is not configured. GEMINI_API_KEY is missing on the server."},
            status=503,
        )

    # Inputs
    photo = request.FILES.get("photo")
    product_id = request.POST.get("product_id")
    if not photo:
        return JsonResponse({"error": "Please upload a room photo first."}, status=400)
    if not product_id:
        return JsonResponse({"error": "Please select a tile first."}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if not product.image:
        return JsonResponse({"error": "This tile has no image to apply."}, status=400)

    # Read both images into memory
    room_bytes = photo.read()
    room_mime = photo.content_type or "image/jpeg"

    try:
        with product.image.open("rb") as fh:
            tile_bytes = fh.read()
    except Exception:
        return JsonResponse({"error": "Could not read the tile image."}, status=500)
    tile_mime = mimetypes.guess_type(product.image.name)[0] or "image/jpeg"

    surface = _surface_for_category(product.category.name if product.category else "")

    prompt = (
        f"You are an interior-design visualizer. The FIRST image is a photo of a real room. "
        f"The SECOND image is a close-up of a ceramic tile texture/pattern. "
        f"Re-render the FIRST image so that the {surface} is fully covered with the tile from the "
        f"SECOND image, laid in a neat realistic grid with thin grout lines. "
        f"Match the room's existing perspective, lighting, shadows and reflections so the tiles "
        f"look naturally installed. Use physically accurate path-traced (ray-traced) lighting "
        f"with global illumination, soft realistic shadows, ambient occlusion in corners, and "
        f"correct light bounce and reflections on the tile surface so the result looks "
        f"photorealistic. Keep everything else in the room (walls, furniture, fixtures, windows) "
        f"exactly the same. Photorealistic result, same camera angle and framing."
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=room_bytes, mime_type=room_mime),
                types.Part.from_bytes(data=tile_bytes, mime_type=tile_mime),
            ],
        )
    except Exception as e:
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "billing" in msg.lower():
            return JsonResponse(
                {
                    "error": "Gemini quota/billing not active for this API key. "
                    "Enable billing at aistudio.google.com, then try again.",
                },
                status=402,
            )
        return JsonResponse({"error": f"AI request failed: {msg[:300]}"}, status=502)

    # Extract the generated image
    try:
        for part in response.candidates[0].content.parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                b64 = base64.b64encode(inline.data).decode("ascii")
                mime = inline.mime_type or "image/png"
                return JsonResponse({"image": f"data:{mime};base64,{b64}"})
    except (IndexError, AttributeError):
        pass

    return JsonResponse(
        {"error": "The AI did not return an image. Try a clearer room photo."},
        status=502,
    )

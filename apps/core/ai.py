"""
AI Room Visualizer helpers — image preparation and the Gemini image-editing call.
"""
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidImage(Exception):
    """The upload isn't a readable JPEG, PNG or WebP image."""


class VisualizerError(Exception):
    """The AI request failed. The message is for the server log, not for users."""


class VisualizerBusy(VisualizerError):
    """The AI provider refused the request because of quota, rate or billing limits."""


def surface_for_category(name):
    """Decide whether a category's tiles go on the floor or the wall."""
    n = (name or "").lower()
    if "wall" in n or "bathroom" in n:
        return "wall"
    return "floor"


def build_prompt(surface):
    return (
        f"You are an interior-design visualizer. The FIRST image is a photo of a real room. "
        f"The SECOND image is a close-up of a tile texture/pattern. "
        f"Re-render the FIRST image so that the {surface} is fully covered with the tile from the "
        f"SECOND image, laid in a neat realistic grid with thin grout lines. "
        f"Match the room's existing perspective, lighting, shadows and reflections so the tiles "
        f"look naturally installed. Use physically accurate path-traced (ray-traced) lighting "
        f"with global illumination, soft realistic shadows, ambient occlusion in corners, and "
        f"correct light bounce and reflections on the tile surface so the result looks "
        f"photorealistic. Keep everything else in the room (walls, furniture, fixtures, windows) "
        f"exactly the same. Photorealistic result, same camera angle and framing."
    )


def prepare_image(fileobj, max_side):
    """
    Check that ``fileobj`` is a real JPEG/PNG/WebP image and return it re-encoded
    as JPEG bytes, shrunk so its longest side is at most ``max_side`` pixels.
    Re-encoding also strips EXIF metadata such as GPS location.
    """
    try:
        fileobj.seek(0)
        with Image.open(fileobj) as probe:
            image_format = probe.format
            probe.verify()
        if image_format not in ALLOWED_FORMATS:
            raise InvalidImage(f"Unsupported image format: {image_format}")
        fileobj.seek(0)
        img = Image.open(fileobj)
        img.load()
    except InvalidImage:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImage(str(exc)) from exc

    try:
        img = ImageOps.exif_transpose(img)  # respect phone camera orientation
    except Exception:
        pass

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        flattened = Image.new("RGB", rgba.size, (255, 255, 255))
        flattened.paste(rgba, mask=rgba.getchannel("A"))
        img = flattened
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    out = BytesIO()
    img.save(out, format="JPEG", quality=88, optimize=True)
    return out.getvalue(), "image/jpeg"


def render_room_with_tile(api_key, prompt, room_bytes, room_mime, tile_bytes, tile_mime):
    """
    Ask Gemini to re-render the room photo with the tile applied.
    Returns (image_bytes, mime_type), or (None, None) if no image came back.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise VisualizerError("The google-genai package is not installed.") from exc

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=room_bytes, mime_type=room_mime),
                types.Part.from_bytes(data=tile_bytes, mime_type=tile_mime),
            ],
        )
    except Exception as exc:
        text = str(exc)
        lowered = text.lower()
        if "resource_exhausted" in lowered or "429" in text or "billing" in lowered or "quota" in lowered:
            raise VisualizerBusy(text) from exc
        raise VisualizerError(text) from exc

    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return inline.data, inline.mime_type or "image/png"
    return None, None

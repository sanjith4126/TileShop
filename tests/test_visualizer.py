"""
AI Room Visualizer hardening (A7). Gemini is always mocked.
"""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.core import ai

from .base import ShopTestCase, image_bytes, image_upload

URL = "/room-visualizer/generate/"


class VisualizerPageTests(ShopTestCase):
    def test_page_shows_unavailable_state_without_api_key(self):
        with self.settings(GEMINI_API_KEY=""):
            response = self.client.get("/room-visualizer/")
        self.assertContains(response, "temporarily unavailable")
        self.assertNotContains(response, 'type="file"')

    def test_page_offers_upload_with_api_key(self):
        with self.settings(GEMINI_API_KEY="test-key"):
            response = self.client.get("/room-visualizer/")
        self.assertContains(response, 'type="file"')

    def test_tile_cards_are_buttons_with_data(self):
        response = self.client.get("/room-visualizer/")
        self.assertContains(response, f'<button type="button" id="tile-card-{self.product.pk}"', html=False)
        self.assertContains(response, 'data-price="520.00"')

    def test_bad_product_parameter_does_not_crash(self):
        for value in ("abc", "-3", "999999999999999999999"):
            self.assertEqual(self.client.get(f"/room-visualizer/?product={value}").status_code, 200)

    def test_preselected_product_shows_price_and_quote_link(self):
        response = self.client.get(f"/room-visualizer/?product={self.product.pk}")
        self.assertContains(response, f'id="quote-link" href="/inquiry/?product={self.product.pk}"')
        self.assertContains(response, "520.00")


@override_settings(GEMINI_API_KEY="test-key", VISUALIZER_RATE_LIMIT=3)
class VisualizerApiTests(ShopTestCase):
    def post(self, photo=None, product=None):
        data = {"product_id": (product or self.product).pk}
        if photo is not False:
            data["photo"] = photo or image_upload("room.jpg", size=(300, 200), fmt="JPEG")
        return self.client.post(URL, data)

    @override_settings(GEMINI_API_KEY="")
    def test_not_configured(self):
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.json())

    def test_rejects_get(self):
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_missing_photo_or_product(self):
        self.assertEqual(self.post(photo=False).status_code, 400)
        response = self.client.post(URL, {"photo": image_upload("room.jpg", fmt="JPEG"), "product_id": "abc"})
        self.assertEqual(response.status_code, 400)

    def test_rejects_non_images(self):
        fake = SimpleUploadedFile("room.jpg", b"<?php echo 'not an image'; ?>", content_type="image/jpeg")
        response = self.post(photo=fake)
        self.assertEqual(response.status_code, 400)
        self.assertIn("JPG, PNG or WebP", response.json()["error"])

    @override_settings(VISUALIZER_MAX_UPLOAD_BYTES=1000)
    def test_rejects_large_uploads(self):
        big = SimpleUploadedFile("room.png", image_bytes(size=(400, 400)), content_type="image/png")
        self.assertEqual(self.post(photo=big).status_code, 413)

    def test_rejects_product_without_image(self):
        self.assertEqual(self.post(product=self.no_category).status_code, 400)

    def test_success_returns_image_and_sends_resized_jpeg(self):
        with mock.patch.object(ai, "render_room_with_tile", return_value=(b"PNGDATA", "image/png")) as call:
            response = self.post(photo=image_upload("room.png", size=(4000, 3000)))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["image"].startswith("data:image/png;base64,"))
        args = call.call_args.args
        self.assertEqual(args[0], "test-key")
        self.assertEqual(args[3], "image/jpeg")  # re-encoded, EXIF stripped
        from io import BytesIO

        from PIL import Image
        with Image.open(BytesIO(args[2])) as sent:
            self.assertLessEqual(max(sent.size), 1600)

    def test_provider_errors_are_not_leaked(self):
        error = ai.VisualizerError("Invalid API key AIzaSecret123 at /srv/app")
        with mock.patch.object(ai, "render_room_with_tile", side_effect=error):
            response = self.post()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("AIzaSecret123", response.content.decode())

    def test_busy_provider(self):
        with mock.patch.object(ai, "render_room_with_tile", side_effect=ai.VisualizerBusy("429 RESOURCE_EXHAUSTED")):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("RESOURCE_EXHAUSTED", response.content.decode())

    def test_rate_limit(self):
        with mock.patch.object(ai, "render_room_with_tile", return_value=(b"IMG", "image/png")):
            statuses = [self.post().status_code for _ in range(4)]
        self.assertEqual(statuses, [200, 200, 200, 429])

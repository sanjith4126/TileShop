"""
Report SEO gaps in the catalogue, the content and the settings. It only reads:
nothing is changed, generated or published.

    python manage.py seo_audit
    python manage.py seo_audit --fail-on-issues    (exit code 1 if any issue is found)

Issues are things to fix (a product without an image, two pages with the same
title). Notes are worth knowing but may be intended (drafts waiting for review,
analytics not set up yet).
"""
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.content.models import Guide, Page
from apps.core.models import BusinessInfo, Category
from apps.products.models import Product
from apps.products.queries import category_product_counts
from apps.products.views import product_title

THIN_DESCRIPTION = 60   # characters
LONG_TITLE = 65         # Google usually shortens titles longer than this
OWNER_PLACEHOLDER = "[OWNER TO CONFIRM]"


class Command(BaseCommand):
    help = ("Report missing descriptions, images, alt text and categories, unclear sizes, "
            "empty categories and duplicate titles. Read-only.")

    def add_arguments(self, parser):
        parser.add_argument("--fail-on-issues", action="store_true",
                            help="Exit with an error if any issue is found.")

    def handle(self, *args, **options):
        self.issues = 0
        self.notes = 0
        titles = defaultdict(list)   # page title -> pages using it

        self.check_products(titles)
        self.check_categories(titles)
        self.check_content(titles)
        self.report("issue", "Pages with the same title", [
            f"{title!r}: {', '.join(pages)}" for title, pages in sorted(titles.items()) if len(pages) > 1
        ])
        self.check_business()
        self.check_settings()

        summary = f"\n{self.issues} issue(s), {self.notes} note(s)."
        self.stdout.write(self.style.SUCCESS(summary) if not self.issues else self.style.WARNING(summary))
        if options["fail_on_issues"] and self.issues:
            raise CommandError(f"{self.issues} SEO issue(s) found.")

    # ── output ──────────────────────────────────────────────────────────
    def heading(self, text):
        self.stdout.write("\n" + self.style.MIGRATE_HEADING(text))

    def report(self, level, title, items):
        """Print one check: nothing when it passes, otherwise the title and each finding."""
        if not items:
            return
        if level == "issue":
            self.issues += len(items)
            self.stdout.write(self.style.WARNING(f"  [!] {title} ({len(items)})"))
        else:
            self.notes += len(items)
            self.stdout.write(f"  [i] {title} ({len(items)})")
        for item in items:
            self.stdout.write(f"      - {item}")

    # ── checks ──────────────────────────────────────────────────────────
    def check_products(self, titles):
        products = list(
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("additional_categories", "gallery")
            .order_by("name")
        )
        self.heading(f"Products ({len(products)} active)")

        names = defaultdict(list)
        long_titles = []
        for product in products:
            names[product.name.strip().lower()].append(product.name)
            title = f"{product_title(product)} | {settings.SITE_NAME}"
            titles[title].append(f"product {product.pk}")
            if len(title) > LONG_TITLE:
                long_titles.append(f"{product.name}: {len(title)} characters")

        self.report("issue", "Not in any category (listed on no category page)", [
            p.name for p in products if not p.all_categories
        ])
        self.report("issue", "No main category (title and breadcrumbs fall back to 'Tile')", [
            f"{p.name} (also in: {', '.join(c.name for c in p.all_categories)})"
            for p in products if p.category is None and p.all_categories
        ])
        self.report("issue", "No main image", [p.name for p in products if not p.image])
        self.report("issue", f"Missing or thin description (under {THIN_DESCRIPTION} characters)", [
            f"{p.name} ({len((p.description or '').strip())} characters)"
            for p in products if len((p.description or "").strip()) < THIN_DESCRIPTION
        ])
        self.report("issue", "Unclear size (left out of titles, alt text and structured data)", [
            f"{p.name}: {p.size!r}" for p in products if p.size and not p.clear_size
        ])
        self.report("issue", "No size", [p.name for p in products if not (p.size or "").strip()])
        self.report("note", "Gallery photos without a caption (their alt text falls back to the product name)", [
            f"{p.name}: {n} photo(s)" for p in products
            if (n := sum(1 for img in p.gallery.all() if not img.caption.strip()))
        ])
        self.report("issue", "Duplicate product names", [
            ", ".join(group) for group in names.values() if len(group) > 1
        ])
        self.report("note", f"Long page titles (over {LONG_TITLE} characters; Google may shorten them)", long_titles)

    def check_categories(self, titles):
        categories = list(Category.objects.order_by("name"))
        counts = category_product_counts()
        self.heading(f"Categories ({len(categories)})")
        for category in categories:
            titles[f"{category.name} | {settings.SITE_NAME}, Bhavani"].append(f"category {category.slug}")
        self.report("issue", "Empty: no active products (the page is noindex and shows the showroom message)", [
            c.name for c in categories if not counts.get(c.id)
        ])
        self.report("issue", "No description", [c.name for c in categories if not (c.description or "").strip()])
        self.report("note", "No image (the homepage shows a placeholder icon)", [c.name for c in categories if not c.image])

    def check_content(self, titles):
        guides = list(Guide.objects.order_by("title"))
        pages = list(Page.objects.order_by("title"))
        self.heading(f"Guides ({len(guides)}) and policy pages ({len(pages)})")
        for item in [g for g in guides if g.is_published] + [p for p in pages if p.is_published]:
            titles[f"{item.title} | {settings.SITE_NAME}"].append(item.get_absolute_url())

        self.report("note", "Guides waiting for review (unpublished)", [g.title for g in guides if not g.is_published])
        self.report("note", "Policy pages waiting for review (unpublished)", [p.title for p in pages if not p.is_published])
        self.report("issue", f"Published with {OWNER_PLACEHOLDER} still in the text", [
            item.title for item in guides + pages
            if item.is_published and OWNER_PLACEHOLDER in (item.body or "")
        ])
        self.report("issue", "Published guides without a summary (used as the meta description)", [
            g.title for g in guides if g.is_published and not (g.summary or "").strip()
        ])
        self.report("note", "Published guides without a cover image", [
            g.title for g in guides if g.is_published and not g.cover_image
        ])
        self.report("note", "Published pages without a meta description", [
            p.title for p in pages if p.is_published and not (p.meta_description or "").strip()
        ])

    def check_business(self):
        info = BusinessInfo.get_solo()
        self.heading("Business details (admin: Business info)")
        if not info.details_confirmed:
            self.report("issue", "Not confirmed", [
                "phone, email and address are kept out of structured data, meta tags and tel:/mailto: links "
                "until 'details confirmed' is ticked"
            ])
        missing = [label for label, value in (
            ("phone", info.phone), ("email", info.email), ("opening hours", info.opening_hours),
            ("opening hours for Google", info.opening_hours_spec), ("street address", info.street_address),
            ("postal code", info.postal_code), ("latitude/longitude", info.latitude and info.longitude),
            ("Google Maps link", info.maps_url), ("WhatsApp number", info.whatsapp),
            ("logo", info.logo), ("share image (1200x630)", info.share_image),
            ("Google Business Profile link", info.google_business_url),
        ) if not value]
        self.report("note", "Not filled in", missing)

    def check_settings(self):
        self.heading("Settings (environment variables)")
        site_url = settings.SITE_URL or ""
        self.report("issue", "SITE_URL", [
            message for condition, message in (
                (not site_url, "not set: canonical URLs and the sitemap use whatever host the request came from"),
                (site_url.startswith("http://"), f"{site_url} uses http; use the https address"),
                (site_url.endswith("/"), "remove the trailing slash"),
            ) if condition
        ])
        self.report("note", "Not configured", [
            name for name, value in (
                ("GOOGLE_SITE_VERIFICATION (Search Console)", settings.GOOGLE_SITE_VERIFICATION),
                ("BING_SITE_VERIFICATION (Bing Webmaster Tools)", settings.BING_SITE_VERIFICATION),
                ("ANALYTICS_PROVIDER / ANALYTICS_ID", settings.ANALYTICS_PROVIDER and settings.ANALYTICS_ID),
                ("SHOP_NOTIFICATION_EMAIL (emails about new orders and quote requests)",
                 settings.SHOP_NOTIFICATION_EMAIL),
            ) if not value
        ])
        if settings.DEBUG:
            self.report("note", "DEBUG is on", ["fine on your computer; it must be off on the live site"])

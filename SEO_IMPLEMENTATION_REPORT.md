# Suwasthik Tiles — SEO implementation report

What was changed on the `seo-optimization` branch of the `tileshop` repository,
why, how it was tested, and what only the owner can do next. Work followed the
specification `suwasthick-tiles-seo-prompt.md` (prompt 1) and the planning
request appended to it (prompt 2). Section numbers such as "A1" or "§9" refer to
that specification.

- Branch: `seo-optimization`, 10 commits, nothing pushed. Database backup taken
  before the first migration: `../tileshop-backups/db-before-seo-2026-10-02.sqlite3`.
- The tiered plan requested in prompt 2 is in
  [SEO_ENHANCEMENT_PLAN.md](SEO_ENHANCEMENT_PLAN.md), with every item's status.
- Deployment steps, including every new setting, are in [DEPLOY.md](DEPLOY.md).

---

## 0. Section A fixes: bugs, security and half-built features

| # | Problem | What was done | Main files |
| --- | --- | --- | --- |
| A1 | Quote requests were thrown away | `Inquiry` model saves every request; Django form with field errors that keeps what was typed; admin list with filters, search and status; confirmation shown once; optional email to the shop | `apps/core/models.py`, `forms.py`, `views.py`, `admin.py`, `notifications.py`, `templates/inquiry/inquiry_form.html` |
| A2 | Order confirmations exposed customer data | Visible only to the session that placed the order or the logged-in owner, otherwise 404; `noindex`; new owner-only order detail page | `apps/orders/views.py`, `urls.py`, `templates/orders/*` |
| A3 | Secret key committed in `DEPLOY.md` | Replaced with a placeholder and the key-generation command. Git history was not rewritten | `DEPLOY.md` |
| A4 | Unused files in public media | Passport photo and `tileshop.zip` moved to the Recycle Bin (owner-approved, 2 Oct). New read-only `find_unused_media` command; it lists `banners/PLATTER1.png` and `products/Screenshot_2026-06-23_093422.png`, which were not deleted | `apps/core/management/commands/find_unused_media.py` |
| A5 | Open redirect after login | Only same-site `next` URLs are followed (`url_has_allowed_host_and_scheme`, HTTPS required in production) | `apps/accounts/views.py` |
| A6 | Bad input caused HTTP 500 | Quantities and IDs are parsed safely and clamped; invalid parameters are ignored or return 404 | `apps/core/utils.py`, `apps/cart/views.py`, `apps/products/views.py`, `apps/core/views.py` |
| A7 | AI visualizer open to abuse; three UI bugs | Size check before reading, Pillow verification, EXIF stripped and image shrunk before sending, rate limit per session and IP, generic errors (details logged), "unavailable" state without a key. Quote link and price now follow the selected tile; tile cards are keyboard-accessible buttons | `apps/core/ai.py`, `apps/core/views.py`, `templates/room_visualizer.html` |
| A8 | Dead, fake and misleading links | Footer marble/granite/slate links replaced by real categories and materials; material and in-stock filters implemented and combined; dashboard "Details" opens a real order page; `#` policy links removed (real pages appear when published); non-clickable social icons removed (real profiles appear when added); fake room presets removed and stock photo labelled; "Admin Panel" link removed from the login page | `templates/base.html`, `templates/products/*`, `templates/accounts/*`, `apps/products/views.py` |
| A9 | Price unit vs cart mismatch | Prices, wording, calculator and cart left unchanged as the owner asked. The unit label is one setting (`PRICE_UNIT_LABEL`/`PRICE_UNIT_CODE`) shared by the page and Product schema. Stock shows only "In stock"/"Out of stock". **Waiting on owner** | `tileshop/settings.py`, `templates/products/product_detail.html`, `apps/core/structured_data.py` |
| A10 | Orders not validated or atomic | Checkout form with validation; order creation inside `transaction.atomic()` with items re-checked; optional email to the shop; one order number format `ST-<n>`; stock is reduced only when `ENFORCE_STOCK_LIMITS=True` | `apps/orders/forms.py`, `views.py`, `models.py`, `admin.py` |
| A11 | Static storage setting ignored on Django 5.2 | `STORAGES` setting; Django pinned to `>=5.2,<5.3`; the test suite also passes in a fresh virtualenv built from `requirements.txt` (Django 5.2.17) | `tileshop/settings.py`, `requirements.txt` |
| A12 | Empty categories were dead ends | Kept, with a true showroom message, quote and showroom links; `noindex,follow` and out of the sitemap until they have an active product (automatic); grammar fixed | `templates/products/product_list.html`, `apps/products/views.py`, `apps/core/sitemaps.py` |
| A13 | Hover-only interface on phones | Product-card buttons, homepage category names and visualizer tile names visible on touch screens; hover effects kept for mouse users | `templates/products/_product_card.html`, `templates/home.html`, `templates/room_visualizer.html` |
| A14 | Unverified and contradictory claims | Kept out of titles, meta tags, structured data and links. Contradictions removed ("natural stone", "100% Natural Materials", marble/granite links). Other claims left visible and listed in section 15 | templates, `apps/core/context_processors.py` |
| A15 | Tailwind Play CDN in production | Tailwind 3.4.19 + forms + container-queries compiled to `static/css/site.css` (pinned, lockfile, built CSS committed); screenshots compared before/after; `bg-white/97` (no CSS generated) fixed | `package.json`, `tailwind.config.js`, `frontend/site.css`, `static/css/site.css` |
| A16 | "TileShop Premium" brand | Admin header/title and the registration message say "Suwasthik Tiles" | `tileshop/urls.py`, `apps/accounts/views.py` |
| A17 | UTC time zone | `Asia/Kolkata` | `tileshop/settings.py` |
| A18 | Logout by plain GET | POST-only with CSRF; the logout links are small forms (there were two, not three) | `apps/accounts/views.py`, `templates/base.html`, `templates/accounts/dashboard.html` |
| A19 | Form problems | Labels connected; checkout and contact `autocomplete`; register keeps the username and uses valid autocomplete values; login and register have an H1 | `templates/inquiry/inquiry_form.html`, `templates/orders/checkout.html`, `templates/accounts/*` |
| A20 | N+1 queries | `select_related`/`prefetch_related`; cart totals calculated once; cart badge is one aggregate query; navigation data cached and cleared on change; tests check query counts don't grow with products | views, `apps/cart/context_processors.py`, `apps/core/context_processors.py` |
| A21 | Icon names read aloud and indexed | Icons drawn from a `data-icon` attribute (no text in the page), `aria-hidden`, icon-only controls named; self-hosted subset of the icons used (15.5 KB instead of 1.14 MB) | all templates, `frontend/site.css`, `scripts/update_fonts.py` |
| A22 | Leftovers | Removed `static/css/styles.css`, `static/js/main.js`, `static/3d/` and django-crispy-forms. `.env` was not edited: remove `SUPABASE_URL` and `SUPABASE_ANON_KEY` yourself | — |
| A23 | Footer year hard-coded 2024 | `{% now "Y" %}` | `templates/base.html` |
| A24 | Bots create sessions and carts | `/cart/` disallowed in robots.txt and `noindex`; viewing the cart no longer creates one; new `clear_stale_carts` command and a daily task in `DEPLOY.md`. Your local database has 22 carts, 14 of them stale; the command was only dry-run on it | `apps/core/views.py`, `apps/cart/views.py`, `apps/cart/management/commands/clear_stale_carts.py` |
| A25 | Deployment docs out of date | `DEPLOY.md` rewritten; `.env.example` lists every variable (names only) | `DEPLOY.md`, `.env.example` |

Found and fixed during the work (not in the specification):

- **Signing in or registering emptied the cart.** Django gives the visitor a new
  session key at login and carts were stored by key. The cart now moves to the
  new key (`apps/accounts/views.py`).
- **The mobile menu was broken.** The header's frosted-glass blur made the
  full-screen menu collapse to 64 px, so its links floated over the page. The
  blur now sits on its own layer (`templates/base.html`).
- **The About page scrolled sideways on phones** (a decorative square, 391 px
  wide page). Clipped (`templates/about.html`).
- **The product-page quantity limit used the stock number** even when stock
  limits are off. It now follows the same rule as the cart.
- **An empty value in `.env` such as `EMAIL_USE_TLS=` turned the setting off.**
  Empty now means "use the default" (`tileshop/settings.py`).
- **The category summary miscounted products** (a bug in this branch's own
  phase 5 code, caught while checking this report): products sharing the same
  material, size and price were counted once, so Floor Tiles said "5 floor
  tiles" instead of 12. Fixed, with a test; the category meta description also
  gained a missing full stop (`apps/products/views.py`).

---

## 1. Executive summary

Before this work the site had no SEO foundation (no meta descriptions,
canonicals, sitemap, robots.txt or structured data), lost every quote request,
showed any customer's order to anyone, and sent phones a 31 MB homepage whose
main image took over two minutes to appear in Lighthouse's mobile test.

Now:

- **Safe to promote.** Quote requests and orders are saved and validated,
  customer data is private, inputs can't crash pages, the AI visualizer is
  protected against abuse, and `check --deploy` reports no issues.
- **Crawlable and indexable.** Clean URLs with 301 redirects from the old
  ones, unique titles and descriptions from real data, canonicals, robots
  rules, an XML sitemap of indexable pages only, real 404 pages, and
  structured data (business, website, breadcrumbs, products with unit prices,
  product lists, FAQ, articles) on every page.
- **Fast and usable on phones.** Homepage weight 31 MB → 0.5 MB, Lighthouse
  accessibility 89–93 → 100, best practices 96 → 100 and SEO 91 → 100 on the
  measured pages; mobile menu, touch labels and tap targets fixed.
- **Findable for real buying questions.** Category landing pages, product
  specification tables, a size-aware site search ("2x2", "60x60",
  "600x1200"), a tile calculator answering "how many tiles do I need", and
  three buying guides plus five policy pages drafted for review (not published).
- **Ready for local search and AI answers** once the owner confirms the
  business details: the phone, address, hours and map are held in one admin
  record and published to Google only after "details confirmed" is ticked.
- **Tested.** 153 automated tests, including a crawl of every internal link.

What remains is mostly business information and decisions only the owner can
provide (section 15): confirming contact details, choosing the domain,
publishing the drafts, adding products to the four empty categories, Google
Business Profile and Search Console.

---

## 2. Initial problems

### Critical

- Quote requests were not saved or sent anywhere (A1).
- `/orders/success/<id>/` showed any customer's name, phone and address;
  order IDs are sequential (A2).
- A real-looking secret key was committed in `DEPLOY.md` (A3).
- A personal passport photo sat in public media (A4).

### High

- No SEO foundation: no meta descriptions, canonicals, robots meta,
  `robots.txt`, sitemap, Open Graph or structured data; the homepage title
  repeated "Bhavani's Finest Tile Atelier" twice; categories existed only as
  `?category=<id>` URLs and products as `/products/<id>/`.
- Homepage: 31 MB, Lighthouse mobile LCP 138.6 s, performance 64 (section 10).
- Open redirect after login (A5); HTTP 500 errors on bad input (A6); an
  uncapped, publicly callable AI endpoint (A7); dead and fake links (A8);
  price-unit mismatch (A9); unchecked, non-atomic checkout (A10); production
  static-files setting silently ignored (A11); empty categories as dead ends
  (A12); hover-only buttons and labels on phones (A13); unverified claims in
  every page title (A14).

### Medium

- Tailwind built in the browser from a CDN (A15); "TileShop Premium" brand
  (A16); UTC time zone (A17); logout by GET (A18); unlabelled form fields
  (A19); N+1 database queries (A20); icon names read out and indexed as text
  (A21); dead files and packages (A22).

### Low

- Footer year "© 2024" (A23); bot-created carts (A24); outdated deployment
  docs (A25).

---

## 3. Changes implemented

| Phase | Commit | What changed |
| --- | --- | --- |
| 0–3 | `a5a3017` | Branch, database backup, audit, tiered plan (`SEO_ENHANCEMENT_PLAN.md`) |
| 4 | `7acb51f` | Section A critical and high fixes (A1–A8, A10, A11, A16–A18), with tests |
| 5 | `1db8508` | Technical SEO: clean URLs and 301s, metadata, canonicals, robots, sitemap, 404/500, favicons, business info record, category landing pages, filters |
| 6 | `c82c25c` | Headings, visible breadcrumbs, JSON-LD on every page |
| 7 | `8ddff27` | Product specifications, product page improvements, site search, tile calculator |
| 8 | `9645b68` | Content app (guides and policy pages as unpublished drafts), GEO statements, local showroom block, analytics event layer |
| 9 | `f04386f` | Compiled CSS, self-hosted fonts and icon subset, WebP renditions, query fixes, accessibility |
| 10 | `e54443c` | Mobile menu, touch labels, sideways scroll, tap targets, two-week carts |
| 11 | `bd4870b` | `seo_audit` and `clear_stale_carts` commands, crawl test, cart kept on sign-in, LCP image priority, HTML validation fixes |
| 12 | (this commit) | `DEPLOY.md`, `.env.example`, this report, plan statuses; empty-setting and category-count fixes |

New modules worth knowing about:

- `apps/core/seo.py`: page titles, descriptions, canonicals and robots rules
  (`page_meta`).
- `apps/core/structured_data.py`: all JSON-LD.
- `apps/core/sitemaps.py`, and the `robots_txt` view in `apps/core/views.py`.
- `apps/core/context_processors.py`: one place for site-wide settings,
  navigation and business details.
- `apps/core/images.py` and `templatetags/image_tags.py`: WebP renditions and
  the `{% responsive_img %}` tag.
- `apps/products/sizes.py` and `search.py`: size parsing ("60x60cm",
  "1200X600mm", "2x2 ft") and site search.
- `apps/content/`: guides and policy pages.
- Management commands: `seo_audit`, `find_unused_media`,
  `build_image_renditions`, `clear_stale_carts`.

---

## 4. Technical SEO

- **URLs.** Categories: `/products/<slug>/` (e.g. `/products/floor-tiles/`).
  Products: `/products/<id>/<slug>/` (e.g. `/products/2/myglamm-grey/`). Old
  `/products/?category=1` and `/products/2/` URLs, and wrong slugs, return a
  single 301 to the right address. Inactive products and unknown categories
  return 404, never a redirect to the homepage.
- **Canonicals** come from `SITE_URL` and never carry query strings, so
  `/inquiry/?product=2` and `/room-visualizer/?product=2` point to
  `/inquiry/` and `/room-visualizer/`. Filtered listings
  (`?material=`, `?in_stock=`) are `noindex,follow` with a canonical to the
  clean category page. The unused `name`, `price` and `room` parameters were
  removed from links (§34).
- **Robots meta.** Indexable pages: `index,follow,max-image-preview:large`.
  `noindex,follow`: search results, empty categories, filtered listings,
  sign-in and registration, and the guides index while no guide is published.
  `noindex,nofollow`: cart, checkout, order pages, dashboard and staff
  previews of drafts.
- **robots.txt** (`/robots.txt`):

  ```text
  User-agent: *
  Disallow: /cart/
  Disallow: /orders/
  Disallow: /room-visualizer/generate/

  Sitemap: https://<SITE_URL>/sitemap.xml
  ```

  All crawlers, including AI crawlers, may crawl the public pages (§29).
- **Sitemap** (`/sitemap.xml`): home, products, about, quote, visualizer and
  calculator pages; categories that have active products; every active
  product with `lastmod`; published guides and policy pages. With today's data
  it lists 22 URLs. Empty categories, drafts, search, cart, account and
  filtered pages are excluded.
- **Status codes.** A 404 page in the site design returns HTTP 404 and links to
  home, products, the quote form, categories with products and search. The
  500 page is self-contained (no database or context processors). Both are
  tested with `DEBUG=False`.
- **Favicons:** `favicon.ico`, SVG icon and Apple touch icon.
- **Static files** are fingerprinted and compressed by WhiteNoise in
  production (checked with `collectstatic` using the production storage: 145
  files, no missing references).
- **Search Console and Bing** verification tags appear only when
  `GOOGLE_SITE_VERIFICATION` / `BING_SITE_VERIFICATION` are set. Setup steps
  are in `DEPLOY.md` §9. On a `pythonanywhere.com` address only a URL-prefix
  property is possible.

---

## 5. On-page SEO

- **Titles and descriptions** are unique and built from real data, for example:
  - Home: "Suwasthik Tiles – Tiles & Sanitaryware Showroom in Bhavani, Tamil Nadu"
  - Category: "Floor Tiles | Suwasthik Tiles, Bhavani"
  - Product: "Myglamm Grey – 60×60 cm Porcelain Floor Tile | Suwasthik Tiles"
    (unclear sizes such as "4/2" are left out)
  - Calculator: "Tile Calculator – How Many Tiles Do I Need? | Suwasthik Tiles"

  Product descriptions state the size, material, kind, price per sq. ft,
  "from Suwasthik Tiles in Bhavani" and "Order online and pay on delivery".
- **Headings:** one H1 per page and a logical order (tested).
- **Breadcrumbs:** visible trails matching the BreadcrumbList markup on
  products (Home › Products › Floor Tiles › Myglamm Grey), categories, the
  listing, visualizer, calculator and guides.
- **Category pages** show the category description and a factual summary from
  the data, e.g. "12 floor tiles in ceramic and porcelain, including 60×60 cm,
  from ₹54 per sq. ft.", plus links to the other categories.
- **Product pages:** material and specification table; optional fields the
  owner can fill in the admin (brand, product code, finish, colour, thickness,
  where to use, slip resistance, care), shown only when filled and never
  guessed; links to every category the product is in; related products; a
  link to the tile calculator.
- **Images:** descriptive alt text from the data ("Myglamm Grey 60×60 cm
  porcelain floor tile"), empty alt text on decorative stock photos,
  descriptive file names for new uploads, a "View full-size image" link for
  texture detail.
- **Internal links:** footer "Shop by Category" and material links, related
  categories, related products, calculator and guide links, and links from the
  404 page. No category, tool or published guide is orphaned (crawl test).
- **Site search** at `/search/` (header and mobile menu) understands sizes as
  buyers type them: "2x2", "60x60", "600x1200 mm", "60 x 120", and word
  variants such as "matte" → "matt". With no exact match it shows the closest
  matches; with none, categories and a quote link.

---

## 6. Structured data

Every page carries one JSON-LD `@graph`:

| Type | Where | Notes |
| --- | --- | --- |
| `Organization` → `Store` | every page | Name, URL, description, logo, social profiles. Address, phone, email, opening hours, map, coordinates and service area are added only after "details confirmed" is ticked in the admin, and the type becomes `Store` |
| `WebSite` | every page | `inLanguage: en-IN`, linked to the organization |
| `BreadcrumbList` | pages with a visible trail | Same items as the visible breadcrumb |
| `Product` + `Offer` | product pages | Image, description, material, category; brand, SKU and colour when filled; price in INR with `UnitPriceSpecification` (1 square foot, unit code `FTK`, from the shared setting); availability; no unclear sizes |
| `ItemList` | product listing, category pages | Product URLs in display order |
| `FAQPage` | tile calculator | Matches the visible FAQ |
| `Article` | published guides | Headline, author, dates, image |

Checks: every page's JSON-LD parses and contains no "None", "null" or empty
values (automated tests); a script checked all 28 sitemap and sample pages for
Google's required properties per type (0 problems). Google's Rich Results Test
needs the live address (`DEPLOY.md` §9).

Deliberately not added:

- **Review / AggregateRating.** Prompt 2 lists "reviews"; prompt 1 rules it
  out, and prompt 1 wins: the homepage testimonials are real, but Google
  ignores reviews a business publishes about itself and can penalise the
  markup. Collect Google Business Profile reviews instead.
- **Shipping and return-policy details** for products: Search Console may show
  these as optional warnings. Add them when the delivery and returns policies
  are confirmed.

Google now shows FAQ rich results only for authoritative government and health
sites, so the FAQ markup mainly helps other search engines and AI systems read
the answers; the visible FAQ is what serves visitors.

---

## 7. GEO (generative engines and AI answers)

- Server-rendered HTML; nothing important needs JavaScript.
- One plain who/what/where/how statement is used in the footer, the About page
  and the Organization description: "Suwasthik Tiles is a tile and
  sanitaryware showroom in Bhavani, Erode district, Tamil Nadu. It sells
  floor, wall, bathroom, kitchen and parking tiles and sanitaryware, takes
  orders online with payment on delivery, and gives quotes on request."
- Factual, data-derived sentences on category and product pages that AI
  systems can quote.
- Contradictions removed (natural stone, marble, granite, slate, terracotta).
- Name, address and phone come from one record, so every page agrees.
- `robots.txt` allows AI crawlers.
- Not added: `llms.txt`. It is an experimental convention with no proven
  effect; it can be added later if you want it.

---

## 8. AEO (answer engines)

- `/tile-calculator/` opens with the direct answer ("Multiply the room's
  length by its width…, add about 10%…, then divide by the area of one tile"),
  with a worked example, a working calculator, the method, and a visible
  five-question FAQ with matching markup.
- Three buying guides are drafted with question-led headings, unpublished:
  "Ceramic vs Porcelain Tiles: What's the Difference?", "How to Choose the
  Right Floor Tile Size" and "Matt vs Glossy Tiles for Bathrooms". They state
  only general facts and mark shop-specific details `[OWNER TO CONFIRM]`.
- Policy pages (privacy, terms of sale, delivery, returns and breakage,
  warranty) are drafted the same way and unpublished.

---

## 9. Local SEO

Done:

- **Business info** (admin → Business info): one record with address,
  structured address, coordinates, Google Maps link, phone, WhatsApp, email,
  opening hours (text and machine-readable), service areas, social profiles,
  logo and share image. Pre-filled with what the site showed, so nothing
  visible changed.
- Footer, About and contact pages use it; empty values (WhatsApp, Maps,
  social) are hidden rather than shown as placeholders.
- A showroom block on the contact page with address, hours and buttons for
  directions, calling and WhatsApp (each appears when its value is set; call
  and email links only after confirmation).
- `Store` structured data with address, hours, coordinates and service area,
  switched on by the "details confirmed" tick.

Waiting on business information: everything in section 15 under "Business
details", plus the Google Business Profile and listings (section 14).

---

## 10. Performance

Lighthouse 12.8.2, mobile emulation with simulated throttling, on the local
Django development server (no compression or cache headers, which production
adds). "Before" is the original code, measured on 2 October; "Phase 9" was
measured right after the performance work; "Final" was measured on 3 October
after all changes.

| Page | Metric | Before | Phase 9 | Final |
| --- | --- | --- | --- | --- |
| Home `/` | Performance | 64 | 88 | 88 |
| | Accessibility | 92 | 100 | 100 |
| | Best practices | 96 | 100 | 100 |
| | SEO | 91 | 100 | 100 |
| | First Contentful Paint | 4.3 s | 2.3 s | 2.3 s |
| | Largest Contentful Paint | 138.6 s | 3.5 s | 3.5 s |
| | Page weight | 31,074 KiB | 501 KiB | 503 KiB |
| Listing `/products/` | Performance | 63 | 81 | 77 |
| | Accessibility | 93 | 100 | 100 |
| | Best practices | 96 | 100 | 100 |
| | SEO | 91 | 100 | 100 |
| | First Contentful Paint | 4.6 s | 2.4 s | 3.5 s |
| | Largest Contentful Paint | 26.7 s | 4.5 s | 4.5 s |
| | Page weight | 7,521 KiB | 583 KiB | 584 KiB |
| Product `/products/2/myglamm-grey/` | Performance | 61 | 74 | 73 |
| | Accessibility | 89 | 100 | 100 |
| | Best practices | 96 | 100 | 100 |
| | SEO | 91 | 100 | 100 |
| | First Contentful Paint | 5.7 s | 3.9 s | 3.9 s |
| | Largest Contentful Paint | 18.9 s | 4.7 s | 4.8 s |
| | Page weight | 4,890 KiB | 714 KiB | 716 KiB |

Final runs: Total Blocking Time 0 ms and Cumulative Layout Shift 0–0.001 on all
three pages. The listing page's lower final score is measurement variation, not
a regression: the Phase 9 code, re-measured on the same machine on 3 October,
also scored 77–78 with a 3.5 s first paint, and three final runs agreed.

What changed: Tailwind compiled to one 55 KB stylesheet instead of the
in-browser CDN build; fonts self-hosted and preloaded (no third-party
render-blocking requests, and visitors' IP addresses are no longer sent to
Google Fonts); icon font reduced to the 48 icons used (1.14 MB → 15.5 KB); WebP
copies of every upload at 400/800/1200 px (34 MB of originals → 2.2 MB of
renditions) served with `srcset`/`sizes`, lazy-loaded below the fold and
prioritised for the main image (including the first product photo on listing
pages, the LCP element on phones); N+1 queries removed.

Remaining lab warnings are mostly the development server's missing compression
and cache headers. After deploying, check with PageSpeed Insights, and use
`DEPLOY.md` §7.5 to confirm static files are cached. Real-user (field) data
appears in Search Console once the site has enough traffic.

---

## 11. Accessibility

Target WCAG 2.2 AA. Lighthouse accessibility is 100 on every measured page
(89–93 before).

- Every form field has a label; errors are shown next to fields; checkout and
  contact forms have `autocomplete`.
- Visible keyboard focus on links, buttons and fields; skip link to the main
  content.
- Contrast: the outline colour token was darkened to pass 4.5:1, plus footer,
  testimonial and hero label colours.
- Icons are hidden from screen readers; icon-only controls have names.
- Mobile menu button exposes `aria-expanded`/`aria-controls`; visualizer tile
  cards are real buttons with `aria-pressed`.
- One H1 per page; descriptive alt text; empty alt on decorative images.
- Touch: hover-only content fixed; quantity buttons 44 px wide; every other
  target is at least 24 px, an inline text link, or meets WCAG 2.2's spacing
  exception (checked at 375 px on 15 pages); no sideways scrolling at 375 px.

Automated checks don't catch everything: a short test with a screen reader
(TalkBack on Android) and keyboard-only use is recommended.

---

## 12. CRO (conversions)

- Quote requests are saved and can email the shop; field errors keep the
  visitor's input.
- Orders are validated and atomic, and can email the shop; customers can see
  their own order details.
- "Add to Cart" is visible on touch screens; categories are labelled on phones;
  the mobile menu works.
- Empty categories invite a quote or showroom visit instead of a dead end.
- Search finds tiles by the sizes buyers type.
- The tile calculator links to floor tiles, the quote form and the
  visualizer; product pages link to the calculator.
- The visualizer's quote link and price follow the selected tile, and it shows
  a quote option when AI is unavailable.
- Carts last two weeks and survive signing in.
- Call, WhatsApp and directions buttons appear as soon as those details are
  confirmed or filled in.
- No pop-ups or overlays were added.

Waiting on the owner (A9): the cart charges price × quantity where one "unit"
means one sq. ft, the cart says "Units", and the calculator's result doesn't
reach the cart. These stay as they are until the price unit is confirmed.

**Analytics** (§25): `data-event` attributes and `static/js/analytics.js` send
`product_view`, `category_view`, `search`, `filter_used`, `add_to_cart`,
`begin_checkout`, `purchase` (order placed), `quote_request` (after a
successful save), `contact_click`, `showroom_direction_click`,
`visualizer_upload` and `visualizer_generate`. Nothing loads and nothing is
sent until `ANALYTICS_PROVIDER` (`ga4` or `plausible`) and `ANALYTICS_ID` are
set. No names, phone numbers, emails or addresses are ever sent.

---

## 13. Visible text changes

Only these texts changed. Everything else, including the unconfirmed claims in
section 15, reads exactly as before.

### Every page

| Where | Before | After |
| --- | --- | --- |
| Browser tab / search result title | "(page name) \| Bhavani's Finest Tile Atelier" | A specific title per page, ending "\| Suwasthik Tiles" (examples in section 5) |
| Header | — | Search icon; search box at the top of the mobile menu |
| Keyboard focus only | — | "Skip to content" link |
| Footer description | "Specializing in high-performance architectural materials for luxury residences and commercial projects. Bhavani, Tamil Nadu." | The business statement quoted in section 7 |
| Footer "Materials" column | Exotic Marble, Polished Granite, Industrial Slate, Custom Ceramic, Terracotta | "Shop by Category": the six categories, plus "All ceramic tiles" and "All porcelain tiles" |
| Footer links | — | "Tile Calculator"; "Buying Guides" (once a guide is published) |
| Footer contact | Address, phone and email as text | Same values; "WhatsApp us" and "Get directions" appear when set |
| Footer social icons | Three icons that did nothing | Removed; real profile links appear when added |
| Footer bottom | "© 2024 …", "Privacy Policy", "Terms of Sale" (dead links) | "© 2026 …" (current year); published policy pages are listed instead |

**Home:** subtitle "Elevating interiors with heritage-rich natural materials
and precision craftsmanship from the heart of Tamil Nadu." → "Floor, wall,
bathroom, kitchen and parking tiles and sanitaryware from our showroom in
Bhavani, Tamil Nadu — order online and pay on delivery, or request a quote."
Category names are now always shown on phones.

**About:** the business statement added under the hero text; stat "100%
Natural Materials" → "6 Product Categories" (the real count); "to make the
artistry of natural stone accessible" → "to make quality tiles and
sanitaryware accessible"; address line "Opp. Kalyana Mandabam, Bhavani, Erode
District, Tamil Nadu" → "… Erode Dt, Tamil Nadu" (the footer's wording, now
shared).

**Product listing and category pages:** "(number) specimens of architectural
surface design — from the heart of Tamil Nadu." → the category description and
a summary such as "12 floor tiles in ceramic and porcelain, including 60×60 cm,
from ₹54 per sq. ft."; material filter, "In Stock Only" and
"Apply" now work; empty category "No Kitchen Tiles tiles available at the
moment. View All Tiles" → "We stock kitchen tiles at our Bhavani showroom /
They aren't listed online yet. Ask us for the current range, sizes and prices,
and we'll help you choose." with "Request a Quote" and "Visit the Showroom";
no-match message "No tiles match these filters" with "Clear Filters"; new
"Explore Other Categories" links; product cards no longer say "Uncategorized".

**Product page:** breadcrumb includes the category; "View full-size image";
badge "UNCATEGORIZED" → e.g. "CERAMIC TILE" for products without a category;
"In Stock — 100 units available" → "In Stock"; specification rows "General" →
"Material", "Stock: 100 units" → "Availability: In stock", plus optional rows
when filled; new line "Not sure how much you need? Use the area calculator
below or our tile calculator."; visualizer teaser "Select Space" room buttons →
"How It Works: 1. Upload a photo of your room 2. This tile is already selected
3. Tap "Fit Tiles With AI""; stock photo captioned "Sample room photo — upload
yours to see this tile in it". Price text unchanged ("₹520.00 / SQ. FT (Incl.
Taxes)").

**Room visualizer:** upload hint adds "(JPG, PNG or WebP, under 10 MB)"; tile
price "₹520.00/sq.ft" → "₹520.00 / sq. ft"; when AI is unavailable: "UPLOAD
UNAVAILABLE", "The AI visualizer is unavailable right now", "Browse our tiles,
or request a quote and we'll help you choose the right one for your room.";
error messages are friendly and generic (e.g. "That photo is too large. Please
upload an image under 10 MB.").

**Request a quote:** placeholder "E.g. Marble for bathroom, Granite for
kitchen..." → "E.g. Matt floor tiles for a bathroom, 60×60 tiles for a living
room..."; tile list "Floor Tiles — ₹520.00/sq.ft" → "Floor Tiles — ₹520.00 /
sq. ft", and no "Uncategorized"; "Please check the highlighted fields below." and per-field
errors; new "Visit Our Showroom" block (name, address, hours, "See the full
range of floor, wall, bathroom, kitchen and parking tiles and sanitaryware in
person.", buttons as details allow); success message shown once.

**Checkout and orders:** "Please check the highlighted fields below." and
per-field errors; order number "#5" → "#ST-5" on the confirmation page
(matching the dashboard); messages such as "Some items are no longer available
and were removed from your cart. Please review your order."

**Accounts:** "Admin Panel →" link removed from the login page; after
registering "Welcome to TileShop Premium." → "Welcome to Suwasthik Tiles.";
dashboard "Details" opens the order.

**Cart:** "Please enter a valid quantity." and "Quantity limited to (number)."
messages.

**New pages:** search (`/search/`), tile calculator (`/tile-calculator/`),
order details (`/orders/<id>/`), 404 page ("We couldn't find that page"), 500
page; guides (`/guides/…`) and policies (`/policies/…`) once published.

---

## 14. Remaining manual work

1. **Search Console and Bing:** verify, submit the sitemap, inspect key URLs
   (`DEPLOY.md` §9).
2. **Google Business Profile:** create or claim it with exactly the website's
   name, address and phone; add photos, hours and the website link; ask real
   customers (such as those quoted on the homepage) for reviews.
3. **Listings with identical details:** Bing Places, Apple Business Connect,
   Justdial, IndiaMART, Sulekha, and the dealer locators of the brands you sell.
4. **Analytics:** choose GA4 or Plausible and set the two variables; update
   the privacy policy's cookie paragraph to match.
5. **Real photos:** showroom, fitted rooms and project photos with clients'
   permission; confirm manufacturer images may be used; replace the stock
   photos on the home, About and product pages.
6. **Approve and publish** the five policy pages and three guides (admin →
   Content), after replacing every `[OWNER TO CONFIRM]`. `seo_audit` flags any
   published page that still contains it.
7. **Choose the domain** (section 15) before submitting to search engines.
8. **Replace the secret key** on any server that used the old one.
9. **Add products** to Wall Tiles, Kitchen Tiles, Parking Tiles and
   Sanitaryware, with photos, sizes and prices. Each category becomes
   indexable automatically with its first active product.
10. **Fix catalogue gaps** reported by `python manage.py seo_audit`: LUXE GREY
    has no category; four products have descriptions under 60 characters
    (JUNGLE LUSH's is "carving matt"); ten products have the size "4/2".
11. **Media:** if `media/` was ever uploaded to PythonAnywhere, delete the
    passport photo there; decide about `banners/PLATTER1.png` and
    `products/Screenshot_2026-06-23_093422.png` (unused; not deleted).
12. **`.env`:** remove `SUPABASE_URL` and `SUPABASE_ANON_KEY` (unused).
13. **Outreach:** local architects, engineers, masons and tile layers (the quote
    form already records referrers), local news, Instagram/YouTube showroom
    videos linking to product pages. No bought or fake links.

---

## 15. ACTION REQUIRED FROM OWNER

**Business details** (enter in admin → Business info, then tick "Details
confirmed"; this publishes them to Google and makes phone and email clickable):

- [ ] Phone: currently shown as +91 98765 43210 (left as is, unconfirmed)
- [ ] Email: currently shown as `studio@suwasthick.com` (left as is, unconfirmed)
- [ ] WhatsApp number
- [ ] Full address with PIN code (shown: "Opp. Kalyana Mandabam, Bhavani, Erode
  Dt, Tamil Nadu")
- [ ] Google Maps link and coordinates of the showroom
- [ ] Opening hours (shown: "Mon–Sat, 9 AM to 7 PM")
- [ ] Areas you deliver to or serve
- [ ] Social media profile links
- [ ] Logo file and a 1200×630 sharing image (until then, product and category
  photos are used for link previews)

**Products and prices:**

- [ ] Price unit: per sq. ft, per box or per piece; sq. ft per box; whether GST
  is included (the cart and calculator wait on this, A9)
- [ ] Are the stock numbers real? If yes, set `ENFORCE_STOCK_LIMITS=True`
- [ ] What the size "4/2" means (it stays out of titles, alt text and schema
  until then)
- [ ] Are the porcelain tiles vitrified (GVT / PGVT / double charge)?
- [ ] Brands you sell (for product fields, schema and dealer listings)
- [ ] Product specifications worth adding in the admin (finish, colour,
  thickness, where to use, slip resistance, care)

**Claims shown on the site but not confirmed** (A14). They are kept out of
titles, descriptions and structured data. Confirm, correct or remove each:

| Claim | Where it appears |
| --- | --- |
| "Since 2014" / "Founded in 2014" | Home story section, About badge and story |
| "10+ Years of Heritage" | Home stats, About stats |
| "40,000+" orders / "over 40,000 successful orders" | Home stats, About stats and story |
| "10-year quality warranty" (what it covers, and who gives it) | Home, About, footer badge and copyright line, cart, contact page, dashboard |
| "Open Mon–Sat, 9 AM to 7 PM" | Footer, About, contact page |
| "Bhavani's Finest Tile Atelier" | Home hero label (removed from all titles) |
| "The Imperial Collection" (no such collection; it shows the featured products) | Home section heading |
| "Every tile is hand-inspected" / "hand-selected" | About, Home |
| "serving clients across India" | About |
| "All prices include premium packaging" | Cart |
| "(Incl. Taxes)" after prices | Product pages |

**Decisions and accounts:**

- [ ] Permanent domain (free plan: `YOURNAME.pythonanywhere.com` only)
- [ ] Analytics tool and ID
- [ ] Google Search Console and Bing verification codes
- [ ] Email (SMTP) details, if you want alerts for new orders and quotes
- [ ] Delivery, returns/breakage, warranty and privacy policy details (to
  complete the drafts)
- [ ] Gemini billing, if the AI visualizer should work
- [ ] New secret key on the server; `ADMIN_URL`

---

## 16. Recommended next actions, in priority order

1. Confirm the business details and tick "Details confirmed" (section 15).
2. Decide the domain, deploy with `DEPLOY.md`, set `SITE_URL`, run
   `check --deploy`, and add the daily clean-up task.
3. Verify Search Console and Bing, submit the sitemap, and test a product page
   and the calculator in the Rich Results Test.
4. Create or claim the Google Business Profile and start asking customers for
   reviews.
5. Review and publish the policy pages, then the three guides.
6. Add products to the four empty categories; give LUXE GREY a category; write
   real descriptions for the short ones.
7. Confirm the price unit, GST and stock, then connect the calculator to the
   cart and fix the "Units" label (A9).
8. Set up analytics, then watch search queries, `quote_request` and `purchase`
   events monthly.
9. Replace stock photos with real showroom and project photos.
10. Build local listings and relationships (section 14); add one guide a month
    from real customer questions.

**Checks that were run** (all passed): 153 automated tests (also in a fresh
virtualenv from `requirements.txt` with Django 5.2.17); `check --deploy` with
production-like settings; `makemigrations --check`; `collectstatic` with the
production storage; HTML validation of 20 page types (html-validate, standard
rules; 2 errors on the visualizer were fixed); structured-data checks on 28
URLs; a crawl of every internal link; screenshots and WCAG 2.2 target-size
checks at 375 px; Lighthouse as in section 10. Checks that need the live address are
listed in `DEPLOY.md` §9.

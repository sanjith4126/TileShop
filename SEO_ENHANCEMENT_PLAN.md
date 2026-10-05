# Suwasthik Tiles — SEO enhancement plan

An implementation-ready plan for the Suwasthik Tiles website (Django project `tileshop`). It covers every search signal Google, Bing and AI answer engines evaluate. Each item is tied to the code that implements it, or to the owner decision it waits on.

- **Impact:** H = high, M = medium, L = low effect on visibility, trust or conversions.
- **Effort:** S = under an hour, M = a few hours, L = a day or more.
- **Owner:** ✋ = needs a business decision or information from the owner.
- **Status:** ✅ done in this branch · ⏳ waiting on owner · 📋 planned next.

**Status on 3 October 2026:** every item that can be done in code is done (✅). Items marked ⏳ need information or a decision from the owner; they are listed with exact steps in section 15 of the implementation report.

Section numbers such as "A1" or "§9" refer to the specification, `suwasthick-tiles-seo-prompt.md`. What was actually changed is described in [SEO_IMPLEMENTATION_REPORT.md](SEO_IMPLEMENTATION_REPORT.md).

---

## Tier 0 — Critical: security, data loss, crashes, dead ends (do first)

| ID | Fix | Why it matters | Impact | Effort | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T0.1 | Save every quote request (`Inquiry` model, form validation, admin, optional email alert) — A1 | The main call to action currently loses every lead | H | M | ✋ SMTP for email alerts | ✅ code · ⏳ owner |
| T0.2 | Order confirmation visible only to the buyer (session/owner check, `noindex`) — A2 | Anyone can read customers' names, phones and addresses | H | S | | ✅ |
| T0.3 | Remove the secret key from `DEPLOY.md` — A3 | A committed key lets anyone forge sessions | H | S | ✋ rotate the server key | ✅ code · ⏳ owner |
| T0.4 | Dry-run report of unused media files — A4 | Files in `media/` are public once uploaded | M | S | ✋ approve deletions | ✅ code · ⏳ owner |
| T0.5 | Block open redirects after login — A5 | Phishing via the site's own login page | H | S | | ✅ |
| T0.6 | No HTTP 500 for bad input (cart quantities, `?category=`, `?product=`) — A6 | Crawlers and users hit error pages; soft errors hurt crawl health | H | S | | ✅ |
| T0.7 | Harden the AI visualizer (size and type checks, rate limit, generic errors, unavailable state) and fix its three UI bugs — A7 | Uncapped Gemini cost; wrong tile and price in quote links | H | M | | ✅ |
| T0.8 | Remove dead and fake links (marble/granite links, `#` policy links, fake room presets, admin link) — A8 | Dead ends and misleading links waste crawl budget and trust | H | M | | ✅ |
| T0.9 | Static files: `STORAGES` setting, pin Django 5.2 — A11 | Production silently skips hashed, compressed static files | M | S | | ✅ |

## Tier 1 — High impact, low–medium effort (technical SEO foundation)

| ID | Fix | Why it matters | Impact | Effort | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T1.1 | `robots.txt` with sitemap line; private paths disallowed — §2 | Crawl control; stops bots creating carts | H | S | | ✅ |
| T1.2 | XML sitemap (static pages, categories with products, products with `lastmod`, published guides and policies) — §2 | Fast, complete discovery | H | S | | ✅ |
| T1.3 | Canonical URLs from `SITE_URL`, tracking parameters stripped — §2, §34 | Consolidates duplicate URLs | H | S | ✋ final domain | ✅ code · ⏳ owner |
| T1.4 | Unique titles and meta descriptions from real data; fix the duplicated homepage title — §4 | Relevance and click-through from results | H | M | | ✅ |
| T1.5 | `noindex` on cart, checkout, orders, accounts, search, filtered and empty pages — §2, §20 | Keeps thin and private pages out of the index | H | S | | ✅ |
| T1.6 | Clean URLs: `/products/<category-slug>/`, `/products/<id>/<slug>/`, with 301s from old URLs — §3, §33 | Descriptive URLs; real category landing pages | H | M | | ✅ |
| T1.7 | Custom 404 (real 404 status) and self-contained 500 pages — §32 | Recovers lost visitors; correct status codes | M | S | | ✅ |
| T1.8 | JSON-LD: Organization/Store, WebSite, BreadcrumbList, Product + Offer (INR, unit price), ItemList — §9 | Rich results and machine understanding | H | M | ✋ confirm address/phone/hours to publish them | ✅ code · ⏳ owner |
| T1.9 | Open Graph and Twitter cards (product images on product pages) — §24 | Good WhatsApp and social previews | M | S | ✋ logo and 1200×630 image | ✅ code · ⏳ owner |
| T1.10 | One clear H1 per page and a logical heading order — §5 | Clear topic signals and screen-reader navigation | M | S | | ✅ |
| T1.11 | Brand consistency ("Suwasthik Tiles" everywhere), time zone `Asia/Kolkata` — A16, A17 | Entity consistency for Google and AI systems | M | S | | ✅ |
| T1.12 | Empty categories: helpful showroom message, `noindex` until products exist — A12 | No dead ends; no thin pages in the index | H | S | ✋ add those products | ✅ code · ⏳ owner |
| T1.13 | Touch-friendly UI: no hover-only buttons or labels — A13 | Mobile-first indexing and mobile conversions | H | S | | ✅ |

## Tier 2 — High impact, medium–high effort (experience, content, discoverability)

| ID | Fix | Why it matters | Impact | Effort | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T2.1 | Responsive WebP images (400/800/1200 px) with `srcset`, lazy loading and `fetchpriority` — §11 | The homepage downloaded 31 MB (now 0.5 MB); LCP was the biggest page-experience problem | H | M | | ✅ |
| T2.2 | Compile Tailwind (no runtime CDN), trim fonts, subset the icon font — §12, A15, A21 | Removes render-blocking work; faster first paint | H | M | | ✅ |
| T2.3 | Category landing pages: intro from `Category.description`, factual summary from data, related categories — §8 | Pages that can rank for "floor tiles", "bathroom tiles" and so on | H | M | | ✅ |
| T2.4 | Product pages: full specification table, breadcrumbs with category, descriptive alt text, optional spec fields for the owner — §7 | Relevance for long-tail product searches and image search | H | M | ✋ fill specs in admin | ✅ code · ⏳ owner |
| T2.5 | Site search at `/search/` with size-aware matching ("2x2", "60x60", "600x1200") — §21 | Product discovery; buyers search by size | M | M | | ✅ |
| T2.6 | Working filters (material, in stock) that combine and stay out of the index — §20 | Usability without duplicate-content explosions | M | S | | ✅ |
| T2.7 | Accessibility pass to WCAG 2.2 AA: labels, focus states, contrast, icon text, keyboard access — §22 | Usability signal and legal hygiene | H | M | | ✅ |
| T2.8 | Business info stored in one place (admin-editable), consistent name/address/phone, hidden empty values — §35, §16 | Local SEO consistency; owner updates without code | H | M | ✋ confirm details | ✅ code · ⏳ owner |
| T2.9 | AEO: tile calculator page with direct answers and visible FAQ; question-led content — §14 | Answer boxes and AI answers for "how many tiles do I need" | H | M | | ✅ |
| T2.10 | GEO: plain factual "who/what/where/how to buy" statements across pages and schema — §15 | AI systems can describe and cite the business accurately | H | S | | ✅ |
| T2.11 | Content system: guides (drafts only) and policy pages (drafts only), Article schema — §17, §18 | Topical authority and trust pages | M | M | ✋ review and publish | ✅ code · ⏳ owner |
| T2.12 | Privacy-safe analytics event layer (no personal data), Search Console and Bing verification tags — §25, §26 | Measurement of what SEO traffic does | M | S | ✋ analytics ID, verification codes | ✅ code · ⏳ owner |

## Tier 3 — Medium impact, ongoing quality

| ID | Fix | Why it matters | Impact | Effort | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| T3.1 | `seo_audit` management command (missing descriptions, images, categories, unclear sizes, duplicate titles) — §36 | Keeps quality high as products are added | M | S | | ✅ |
| T3.2 | Automated tests for every fix plus a broken-link crawl — §37 | Prevents regressions | M | M | | ✅ |
| T3.3 | Deployment docs: new settings, CSS build, image renditions, scheduled cleanup (`clear_stale_carts`) — A24, A25 | Repeatable, safe deploys | M | S | | ✅ |
| T3.4 | Remove leftovers (old CSS/JS, unused crispy-forms) — A22 | Less confusion, smaller deploys | L | S | ✋ remove unused Supabase keys from `.env` | ✅ code · ⏳ owner |
| T3.5 | Longer cart lifetime (two weeks) — §19 | Tile purchases take days; carts were lost after 24 h | M | S | | ✅ |
| T3.6 | Found in testing: mobile menu overlay collapsed to 64 px under the blurred header | Phone visitors couldn't use the menu | H | S | | ✅ |
| T3.7 | Found in testing: signing in or registering emptied the cart | Lost carts at the moment of highest intent | H | S | | ✅ |
| T3.8 | Found in testing: first listing photo (the LCP element on phones) was lazy-loaded; category summary miscounted identical products | Slower main paint; wrong product count in text and meta description | M | S | | ✅ |

## Tier 4 — Owner decisions and off-page work (cannot be done in code)

| ID | Action | Why it matters | Impact | Effort | Status |
| --- | --- | --- | --- | --- | --- |
| T4.1 | Confirm phone, email, full address with PIN, Google Maps link, opening hours, then tick "details confirmed" in admin | Unlocks Store schema, `tel:`/`mailto:` links and directions | H | S | ⏳ |
| T4.2 | Create or claim the Google Business Profile with the same name/address/phone; ask real customers for reviews | Most important local ranking factor for a showroom | H | M | ⏳ |
| T4.3 | Choose the permanent domain (custom domain needs a paid PythonAnywhere plan) | Rankings build on the domain; moving later needs 301s | H | S | ⏳ |
| T4.4 | Add products to Wall, Kitchen, Parking Tiles and Sanitaryware | Those category pages become indexable automatically | H | M | ⏳ |
| T4.5 | Confirm price unit (sq.ft, box or piece), GST inclusion and stock numbers | Accurate cart, schema and calculator | H | S | ⏳ |
| T4.6 | Fill product specifications in admin (finish, colour, thickness, application, brand, SKU) | Richer product pages and schema | M | M | ⏳ |
| T4.7 | Review and publish the policy pages and the draft guides | Trust signals; topical content | M | M | ⏳ |
| T4.8 | Real photos of the showroom and fitted rooms; confirm manufacturer images may be used | Image search, E-E-A-T, replaces stock photos | M | M | ⏳ |
| T4.9 | Analytics ID, Search Console and Bing verification codes, then submit the sitemap | Measurement and indexing control | M | S | ⏳ |
| T4.10 | Citations with identical details: Justdial, IndiaMART, Sulekha, Bing Places, Apple Business Connect; brand dealer locators | Local authority and consistency | M | M | ⏳ |
| T4.11 | Rotate the secret key if it was used; delete the passport photo from the server if `media/` was uploaded; approve unused-media deletions | Security and privacy | H | S | ⏳ |

---

## Keyword → page map (one intent, one page)

| Search intent (examples) | Target page | Notes |
| --- | --- | --- |
| Brand: "Suwasthik Tiles", "Suwasthik Tiles Bhavani" | `/` (and `/about/`) | Organization schema, consistent name |
| Local: "tiles shop in Bhavani", "tile showroom near me" | `/` + Google Business Profile | No town doorway pages |
| "floor tiles", "floor tiles price per sq ft", "60x60 floor tiles" | `/products/floor-tiles/` | Data-driven summary with sizes and price range |
| "bathroom tiles", "bathroom tiles price", "matt bathroom tiles" | `/products/bathroom-tiles/` | |
| "wall tiles", "kitchen tiles", "parking tiles", "sanitaryware" | `/products/wall-tiles/` etc. | Indexable once each has products (T4.4) |
| "buy tiles online", "ceramic tiles", "porcelain tiles" | `/products/` | Material filters stay `noindex` |
| "1200x600 tiles", "wood look tiles", "marble look tiles" | the matching product pages | Long-tail product intent |
| "how many tiles do I need", "tile calculator", "tile wastage %" | `/tile-calculator/` | The only page for calculation intent, so no separate "how to calculate" guide |
| "ceramic vs porcelain tiles" | `/guides/ceramic-vs-porcelain-tiles/` (draft) | Publish after owner review |
| "what size floor tile for my room" | `/guides/choosing-floor-tile-size/` (draft) | Publish after owner review |
| "matt vs glossy bathroom tiles" | `/guides/matt-vs-glossy-bathroom-tiles/` (draft) | Publish after owner review |
| "tile visualizer", "see tiles in my room" | `/room-visualizer/` | Unique tool; works once Gemini billing is active |
| "tile quote", "contact Suwasthik Tiles" | `/inquiry/` | Showroom block plus the quote form |

Not targeted, because the shop doesn't sell them: outdoor tiles, marble, granite, slate, terracotta. "Vitrified" and "anti-skid" are used only after the owner confirms them.

## Signals checklist

| Signal group | Covered by |
| --- | --- |
| Crawl and index control | T1.1, T1.2, T1.3, T1.5, T1.6, T1.7, T0.6 |
| Relevance (titles, headings, content, internal links) | T1.4, T1.10, T2.3, T2.4, T2.10, keyword map |
| Page experience (Core Web Vitals, mobile, HTTPS, no intrusive pop-ups) | T2.1, T2.2, T1.13, T2.7; HTTPS and HSTS were already enforced |
| Structured data | T1.8, T2.9 (visible FAQ), T2.11 (Article) |
| Local signals | T2.8, T4.1, T4.2, T4.10 |
| Trust / E-E-A-T | T2.11, T4.7, T4.8, real testimonials kept (no fake review markup) |
| AI / answer engines | T2.9, T2.10, server-rendered HTML, open robots.txt |
| Conversion and measurement | T0.1, T0.7, T2.5, T2.12, T3.5 |

### Review markup

The homepage testimonials are genuine, but Google doesn't show review rich results for reviews a business publishes about itself, so no `Review`/`AggregateRating` markup is added. To earn review stars, collect Google Business Profile reviews (T4.2), or add a real per-product review system later; mark up only genuine, visible product reviews.

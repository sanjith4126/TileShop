# Deploying Suwasthick Tiles on PythonAnywhere

This puts the site online on PythonAnywhere's free plan, keeping the SQLite
database and uploaded tile images between visits. No credit card is needed.

> The site will live at `https://YOURNAME.pythonanywhere.com`.
> Replace `YOURNAME` everywhere below with your PythonAnywhere username.

---

## Before you start

- **Choose the permanent address now.** Search rankings build up on one
  address. The free plan only offers `YOURNAME.pythonanywhere.com`; your own
  domain (for example `www.suwasthicktiles.com`) needs a paid plan. Moving later
  means keeping 301 redirects from the old address running.
- **Use a new secret key.** An earlier version of this file contained a real
  `DJANGO_SECRET_KEY`. It is still in the git history, so never use it. Step 4
  shows how to make a new one.
- **Check for unused images.** On your computer, run
  `python manage.py find_unused_media`. It lists files in `media/` that no
  product, category, banner or guide uses, and deletes nothing. Everything in
  `media/` becomes publicly downloadable once uploaded, so remove anything
  private before step 2.

---

## 1. Create the account

1. Sign up for free at
   <https://www.pythonanywhere.com/registration/register/beginner/>.
2. Confirm your email address and log in.

---

## 2. Get the code onto PythonAnywhere

**Option A: git (recommended, makes updates easy).** In a PythonAnywhere
**Bash console** (Consoles tab):

```bash
git clone https://github.com/YOURNAME/tileshop.git ~/tileshop
```

**Option B: upload a zip.**

1. On your computer, zip the `tileshop` folder **without** these folders and
   files: `.venv/`, `venv/`, `node_modules/`, `staticfiles/`, `__pycache__/`
   and `.env`.
2. PythonAnywhere → **Files** tab → upload the zip to your home folder.
3. In a Bash console, unzip it so that `manage.py` ends up directly inside
   `~/tileshop`:

   ```bash
   unzip tileshop.zip -d ~/tileshop
   ```

**First deploy only: bring your data.** Upload your local `db.sqlite3` and the
`media/` folder into `~/tileshop/` so products, categories, images and orders
carry over. You can leave out `media/renditions/`; step 5 rebuilds it. After the
site is live, never upload your local `db.sqlite3` again: it would overwrite
real orders and quote requests.

---

## 3. Create the virtualenv and install packages

```bash
cd ~/tileshop
python3.11 -m venv venv          # Python 3.10 or newer works
source venv/bin/activate
pip install -r requirements.txt
```

The server does not need Node.js: the stylesheet is built on your computer and
committed (see "Changing the design" below).

---

## 4. Create the server `.env` file

Generate a secret key first and copy the output:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Then create the file:

```bash
cd ~/tileshop
nano .env
```

Paste the template below and fill it in. Lines starting with `#` are comments.
Save with `Ctrl+O`, Enter, then leave with `Ctrl+X`.

```ini
# ── Required ─────────────────────────────────────────────
DEBUG=False
DJANGO_SECRET_KEY=paste-the-new-key-here
ALLOWED_HOSTS=YOURNAME.pythonanywhere.com
# The public address, without a trailing slash. Used for canonical
# links, the sitemap, structured data and link previews.
SITE_URL=https://YOURNAME.pythonanywhere.com

# ── Recommended ──────────────────────────────────────────
# Moves the admin away from /admin/, e.g. ADMIN_URL=manage-7f3k/
ADMIN_URL=

# ── Email alerts for new orders and quote requests (optional) ──
# Without EMAIL_HOST nothing is emailed; everything is still saved in the admin.
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=
SHOP_NOTIFICATION_EMAIL=

# ── Search engines and analytics (optional) ──────────────
# Only the content="..." value of the verification meta tag.
GOOGLE_SITE_VERIFICATION=
BING_SITE_VERIFICATION=
# ga4 (ANALYTICS_ID=G-XXXXXXX) or plausible (ANALYTICS_ID=your domain).
# Nothing loads unless both are set.
ANALYTICS_PROVIDER=
ANALYTICS_ID=

# ── Shop (optional) ──────────────────────────────────────
# True only once the stock numbers in the admin are real: carts are then
# limited to the stock and orders reduce it.
ENFORCE_STOCK_LIMITS=False

# ── AI Room Visualizer (optional, needs Gemini billing) ──
GEMINI_API_KEY=
# At most this many AI images per visitor per window (seconds).
VISUALIZER_RATE_LIMIT=5
VISUALIZER_RATE_WINDOW=3600
```

Keep `.env` private: never commit it, email it or paste it into a chat.

---

## 5. Prepare the database and files

```bash
cd ~/tileshop
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py build_image_renditions
python manage.py createsuperuser        # skip if you uploaded db.sqlite3
python manage.py check --deploy
```

- `migrate` adds the new tables (quote requests, business info, guides and
  policy pages) without touching existing data.
- `collectstatic` copies the stylesheet, fonts and icons into `staticfiles/`
  with fingerprinted names, so browsers can cache them safely.
- `build_image_renditions` makes the small WebP versions of every uploaded
  image that the pages use. New uploads get them automatically.
- `check --deploy` must say "System check identified no issues".

---

## 6. Configure the web app

1. **Web** tab → **Add a new web app** → **Manual configuration** → choose the
   same Python version as the virtualenv.
2. Set:
   - **Source code:** `/home/YOURNAME/tileshop`
   - **Working directory:** `/home/YOURNAME/tileshop`
   - **Virtualenv:** `/home/YOURNAME/tileshop/venv`
3. Open the **WSGI configuration file** link and replace its contents with:

   ```python
   import os
   import sys

   path = "/home/YOURNAME/tileshop"
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ["DJANGO_SETTINGS_MODULE"] = "tileshop.settings"

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

4. Under **Static files**, add:

   | URL        | Directory                             |
   |------------|---------------------------------------|
   | `/static/` | `/home/YOURNAME/tileshop/staticfiles` |
   | `/media/`  | `/home/YOURNAME/tileshop/media`       |

5. Make sure **Force HTTPS** is on (Web tab, "Security" section).

---

## 7. Go live and check

1. Click the green **Reload** button on the Web tab and open
   `https://YOURNAME.pythonanywhere.com`.
2. Check that these open: `/robots.txt`, `/sitemap.xml`, a product page, a
   category page and `/tile-calculator/`.
3. Open the admin (`/admin/`, or your `ADMIN_URL`) → **Business info**. Correct
   the address, phone, email and opening hours, add the Google Maps link,
   WhatsApp number and social profiles, then tick **Details confirmed**. Until
   then the phone and email show as plain text and are left out of Google's
   structured data.
4. Run `python manage.py seo_audit` in the console. It lists what still needs
   attention (products without a category, unclear sizes, empty categories,
   drafts waiting for review). It changes nothing.
5. Static file caching: in the home page's source, find the stylesheet address
   (`/static/css/site.<code>.css`) and run
   `curl -sI https://YOURNAME.pythonanywhere.com/static/css/site.<code>.css`.
   If the response has no long `Cache-Control` header, delete the `/static/`
   mapping from step 6 and reload: WhiteNoise (already installed) then serves
   those files compressed, with one-year caching. Keep the `/media/` mapping
   either way.

---

## 8. Daily clean-up task

Bots and one-time visitors leave behind sessions and empty carts. On the
**Tasks** tab, add a daily task:

```bash
cd /home/YOURNAME/tileshop && venv/bin/python manage.py clearsessions && venv/bin/python manage.py clear_stale_carts
```

`clear_stale_carts` only deletes carts whose session has ended; orders are never
touched. Add `--dry-run` to see the count without deleting anything.

---

## 9. Tell search engines about the site

**Google Search Console** (free):

1. Go to <https://search.google.com/search-console> → **Add property** → choose
   **URL prefix** and enter `https://YOURNAME.pythonanywhere.com/`. (A "Domain"
   property needs DNS access, which a `pythonanywhere.com` address doesn't
   give you.)
2. Choose the **HTML tag** method. Copy only the `content="…"` value into
   `GOOGLE_SITE_VERIFICATION` in `.env`, click **Reload** on the Web tab, then
   click **Verify**.
3. **Sitemaps** → submit `sitemap.xml`.
4. Use **URL Inspection** on the home page and one product page, and request
   indexing.

**Bing Webmaster Tools:** at <https://www.bing.com/webmasters>, choose
**Import from Google Search Console**; nothing else is needed. Or verify with
the meta tag method and `BING_SITE_VERIFICATION`. Bing Webmaster Tools also
covers Yahoo and DuckDuckGo results. IndexNow, which pings Bing and Yandex when
pages change, is optional and not set up.

**After deploying, test with public tools** (they need the live address):

- Rich Results Test: <https://search.google.com/test/rich-results> (a product
  page, `/tile-calculator/`, and a guide once published)
- Schema Markup Validator: <https://validator.schema.org/>
- PageSpeed Insights: <https://pagespeed.web.dev/> (home, a category and a
  product page, mobile)

**Google Business Profile** matters most for a showroom: create or claim it at
<https://business.google.com/> with exactly the same name, address and phone as
the website, and add the website address.

---

## Updating the site later

On your computer, commit the changes (and rebuild the CSS first if templates
changed; see below). Then on PythonAnywhere:

```bash
cd ~/tileshop
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Click **Reload** on the Web tab. Before a large update, download a copy of
`db.sqlite3` from the **Files** tab as a backup.

---

## Changing the design (on your computer only)

The stylesheet `static/css/site.css` is built from `frontend/site.css` and the
templates with Tailwind CSS, and committed to git. It needs Node.js on your
computer, never on the server.

```bash
npm ci                     # first time only: installs the pinned Tailwind
npm run build:css          # after changing classes in any template
npm run watch:css          # optional: rebuild automatically while editing
```

Fonts and icons are self-hosted. After adding a new Material Symbols icon to a
template (`data-icon="…"`), run `python scripts/update_fonts.py` and then
`npm run build:css`, so the icon font includes it.

Run the tests before deploying: `python manage.py test tests`.

---

## Notes and limits (free plan)

- **AI Room Visualizer:** shows as unavailable until `GEMINI_API_KEY` is set and
  Gemini billing is enabled. Each visitor can create `VISUALIZER_RATE_LIMIT`
  images per `VISUALIZER_RATE_WINDOW` seconds. Room photos are sent to Google's
  Gemini API; the draft privacy policy says so.
- Free web apps must be extended with one click every three months
  (PythonAnywhere emails a reminder).
- SQLite is fine for a shop of this size. The code also works with PostgreSQL.
- A custom domain needs a paid plan.

---

## Security

Already enforced when `DEBUG=False`: HTTPS redirect, HSTS (one year), secure
and HttpOnly cookies, CSRF protection for your domain, clickjacking and
MIME-sniffing protection, upload size limits, POST-only logout, login redirects
only to this site, and order pages visible only to the buyer.
`python manage.py check --deploy` reports no issues with production settings.

To do on the server:

- Use a new `DJANGO_SECRET_KEY` (see "Before you start").
- Set `ADMIN_URL` so the admin isn't at the well-known `/admin/` address.
- Remove `SUPABASE_URL` and `SUPABASE_ANON_KEY` from every `.env`: no code uses
  Supabase.
- If `media/` was uploaded before 2 October 2026, delete
  `media/banners/SANJITH_passport_photo.jpeg` from the server (Files tab). It
  was removed from the project because it is a personal photo that nothing on
  the site uses.

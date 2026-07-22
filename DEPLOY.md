# Deploying Suwasthick Tiles (free) on PythonAnywhere

This deploys the site **free**, keeping your SQLite database and uploaded tile
images persistent. No credit card required.

> Your app will live at: `https://YOURNAME.pythonanywhere.com`
> (replace `YOURNAME` everywhere below with your PythonAnywhere username).

---

## 0. One-time: create the account
1. Sign up free at https://www.pythonanywhere.com/registration/register/beginner/
2. Verify your email and log in.

---

## 1. Get the code onto PythonAnywhere

**Option A — upload a zip (simplest):**
1. On your PC, zip the whole `tileshop` folder **except** `venv/`, `staticfiles/`, and `__pycache__/`.
2. PythonAnywhere → **Files** tab → upload the zip into your home folder.
3. Open a **Bash console** (Consoles tab) and unzip:
   ```bash
   unzip tileshop.zip -d ~/tileshop
   ```
   (Adjust so the project ends up at `~/tileshop` with `manage.py` directly inside it.)

**Option B — git (if you push this repo to GitHub):**
```bash
git clone https://github.com/YOURNAME/tileshop.git ~/tileshop
```

Bring your **data**: also upload your local `db.sqlite3` and the whole `media/`
folder into `~/tileshop/` so your products, categories, images and orders carry over.

---

## 2. Create the virtualenv & install packages
In a Bash console:
```bash
cd ~/tileshop
python3.10 -m venv venv          # or python3.11 if offered
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Create the production `.env` file
Still in the console:
```bash
cd ~/tileshop
nano .env
```
Paste this (use YOUR username in ALLOWED_HOSTS):
```
DEBUG=False
DJANGO_SECRET_KEY=gwXbKvw2C7b_6KjMc2ihOVzpOB7PN__XEuehHF2WivFZi4LibtCb71jFqyB2f6X1Ei8
ALLOWED_HOSTS=YOURNAME.pythonanywhere.com
```
Save: `Ctrl+O`, Enter, then `Ctrl+X`.

> The secret key above was generated fresh for you. To make your own instead:
> `python -c "import secrets; print(secrets.token_urlsafe(50))"`

---

## 4. Migrate, collect static, create admin login
```bash
cd ~/tileshop
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser    # skip if you uploaded your db.sqlite3
```

---

## 5. Configure the Web app
1. Go to the **Web** tab → **Add a new web app** → choose **Manual configuration**
   → pick the **same Python version** as your venv (3.10/3.11).
2. In the Web tab, set:
   - **Source code:** `/home/YOURNAME/tileshop`
   - **Working directory:** `/home/YOURNAME/tileshop`
   - **Virtualenv:** `/home/YOURNAME/tileshop/venv`
3. Click the **WSGI configuration file** link and replace its contents with:
   ```python
   import os, sys
   path = '/home/YOURNAME/tileshop'
   if path not in sys.path:
       sys.path.insert(0, path)
   os.environ['DJANGO_SETTINGS_MODULE'] = 'tileshop.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
   Save it.
4. Scroll to **Static files** and add two mappings:
   | URL | Directory |
   |-----|-----------|
   | `/static/` | `/home/YOURNAME/tileshop/staticfiles` |
   | `/media/`  | `/home/YOURNAME/tileshop/media` |

---

## 6. Go live
Click the big green **Reload** button at the top of the Web tab.
Visit **https://YOURNAME.pythonanywhere.com** 🎉

---

## Updating the site later
After changing code or uploading new files:
```bash
cd ~/tileshop
source venv/bin/activate
git pull            # if using git
python manage.py migrate
python manage.py collectstatic --noinput
```
Then click **Reload** on the Web tab.

---

## Notes & limits (free tier)
- **AI Room Visualizer** stays disabled until you enable Gemini billing and add
  `GEMINI_API_KEY=...` to the server `.env`. Everything else works fully.
- Free apps show a reminder to click a "still running" button every ~3 months.
- SQLite is fine for a small shop's traffic. If you outgrow it, the settings are
  already PostgreSQL-compatible.
- Custom domain (e.g. `www.suwasthicktiles.com`) needs a paid plan; the free
  `pythonanywhere.com` subdomain works for launch.

## Security (already hardened ✅)
- `DEBUG=False` in production, secret key from env, locked `ALLOWED_HOSTS`.
- HTTPS forced, HSTS (1 yr), secure + HttpOnly cookies, clickjacking blocked,
  MIME-sniff protection, CSRF trusted origins, upload size cap.
- Verified with `python manage.py check --deploy` → **0 issues**.

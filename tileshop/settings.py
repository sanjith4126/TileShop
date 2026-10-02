"""
Django settings for the Suwasthick Tiles website (project package: tileshop).
Production-ready configuration with SQLite default, PostgreSQL compatible.

All secrets and environment-specific values are read from environment
variables (optionally via a local .env file). Nothing sensitive is hard-coded.
"""
import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if python-dotenv is installed (safe no-op otherwise).
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


def _env_bool(name, default="False"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# True while running `manage.py test`.
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DEBUG", "False")

# SECURITY WARNING: keep the secret key used in production secret!
# In production the key MUST come from the environment. A weak fallback is only
# allowed for local development (DEBUG=True).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "django-insecure-local-dev-only-do-not-use-in-production"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY environment variable is required when DEBUG is off."
        )

# Hosts allowed to serve this site. Comma-separated env var, e.g.
# ALLOWED_HOSTS="yourname.pythonanywhere.com,www.example.com"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"] if DEBUG else []

# Trust the HTTPS origin(s) of the real domain(s) for CSRF.
CSRF_TRUSTED_ORIGINS = [
    "https://" + h for h in ALLOWED_HOSTS
    if h not in ("localhost", "127.0.0.1", "[::1]")
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "apps.core.apps.CoreConfig",
    "apps.products.apps.ProductsConfig",
    "apps.cart.apps.CartConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.content.apps.ContentConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tileshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.cart.context_processors.cart_count",
                "apps.core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "tileshop.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,  # Wait up to 20s for locked DB instead of failing instantly
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization — the shop is in Tamil Nadu, so show Indian time.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# File storage. STORAGES replaced STATICFILES_STORAGE, which Django 5.1+ ignores.
# WhiteNoise gives hashed, compressed static files in production; tests use the
# plain storage so they don't need `collectstatic` first.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
# If a deploy forgets `collectstatic`, serve unhashed URLs instead of failing.
WHITENOISE_MANIFEST_STRICT = False
if TESTING:
    import warnings
    # Tests don't run collectstatic, so STATIC_ROOT doesn't exist.
    warnings.filterwarnings("ignore", message="No directory at")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Admin lives at /admin/ unless ADMIN_URL is set (e.g. "manage-7f3k/").
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/").strip().strip("/") + "/"

# Authentication URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Session settings
# Two weeks (Django's default): tile purchases often take several days, and the
# cart lives in the session. Activity keeps extending it.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_SAVE_EVERY_REQUEST = True

# ─────────────────────────────────────────────────────────────────────
# Security hardening
# ─────────────────────────────────────────────────────────────────────
# Always-on protections
SECURE_CONTENT_TYPE_NOSNIFF = True          # block MIME-sniffing attacks
SECURE_REFERRER_POLICY = "same-origin"      # don't leak URLs to other sites
X_FRAME_OPTIONS = "DENY"                     # block clickjacking (no framing)
SESSION_COOKIE_HTTPONLY = True               # JS can't read the session cookie
CSRF_COOKIE_HTTPONLY = True                  # JS can't read the CSRF cookie
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Caps the size of a request's non-file data (form fields, JSON) at 10 MB.
# File uploads are NOT limited by this setting: views that accept files check
# the file size themselves (see VISUALIZER_MAX_UPLOAD_BYTES).
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
# Uploads bigger than this are streamed to a temporary file instead of memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Production-only protections (enabled automatically when DEBUG is off).
if not DEBUG:
    # The host (e.g. PythonAnywhere) terminates TLS and forwards this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = not TESTING        # force HTTP -> HTTPS
    SESSION_COOKIE_SECURE = True             # cookies only over HTTPS
    CSRF_COOKIE_SECURE = True
    # HTTP Strict Transport Security — tell browsers "HTTPS only" for 1 year.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ─────────────────────────────────────────────────────────────────────
# Email (optional). Without EMAIL_HOST no email is sent; quote requests and
# orders are always saved and visible in the admin.
# ─────────────────────────────────────────────────────────────────────
EMAIL_HOST = os.environ.get("EMAIL_HOST", "").strip()
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = _env_int("EMAIL_PORT", 587)
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", "True")
    EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", "False")
    EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "").strip() or "webmaster@localhost"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
# Where new quote requests and orders are announced.
SHOP_NOTIFICATION_EMAIL = os.environ.get("SHOP_NOTIFICATION_EMAIL", "").strip()

# ─────────────────────────────────────────────────────────────────────
# SEO and measurement (all optional, from the environment)
# ─────────────────────────────────────────────────────────────────────
SITE_NAME = "Suwasthick Tiles"
# The site's public address, used for canonical URLs, the sitemap and
# structured data, e.g. https://yourname.pythonanywhere.com (no trailing slash).
# Without it, the address of the incoming request is used.
SITE_URL = os.environ.get("SITE_URL", "").strip().rstrip("/")
# Verification codes from Google Search Console / Bing Webmaster Tools
# (only the content="..." value of their meta tag).
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
BING_SITE_VERIFICATION = os.environ.get("BING_SITE_VERIFICATION", "").strip()
# Analytics: ANALYTICS_PROVIDER is "ga4" (ANALYTICS_ID = G-XXXXXXX) or
# "plausible" (ANALYTICS_ID = your domain). Nothing loads unless both are set.
ANALYTICS_PROVIDER = os.environ.get("ANALYTICS_PROVIDER", "").strip().lower()
ANALYTICS_ID = os.environ.get("ANALYTICS_ID", "").strip()

# ─────────────────────────────────────────────────────────────────────
# Shop settings
# ─────────────────────────────────────────────────────────────────────
PRICE_CURRENCY = "INR"
# The unit every product price refers to. Shown after prices ("₹54 / sq. ft")
# and used in Product structured data. Change both lines together if the
# pricing unit changes.
PRICE_UNIT_LABEL = "sq. ft"
PRICE_UNIT_CODE = "FTK"  # UN/CEFACT code for square foot
# Limit cart quantities to Product.stock and decrement stock on orders.
# Off until the stock numbers in the admin are confirmed to be real.
ENFORCE_STOCK_LIMITS = _env_bool("ENFORCE_STOCK_LIMITS", "False")
MAX_CART_QUANTITY = 10000

# ─────────────────────────────────────────────────────────────────────
# AI Room Visualizer (Gemini). Disabled unless GEMINI_API_KEY is set.
# ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VISUALIZER_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
VISUALIZER_MAX_IMAGE_SIDE = 1600  # longest side sent to the AI, in pixels
# At most VISUALIZER_RATE_LIMIT generations per visitor per window (seconds).
VISUALIZER_RATE_LIMIT = _env_int("VISUALIZER_RATE_LIMIT", 5)
VISUALIZER_RATE_WINDOW = _env_int("VISUALIZER_RATE_WINDOW", 3600)

# ─────────────────────────────────────────────────────────────────────
# Logging: our own warnings and errors go to the console (the PythonAnywhere
# error/server log).
# ─────────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "apps": {
            "handlers": ["null" if TESTING else "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

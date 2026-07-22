"""
Django settings for TileShop Premium project.
Production-ready configuration with SQLite default, PostgreSQL compatible.

All secrets and environment-specific values are read from environment
variables (optionally via a local .env file). Nothing sensitive is hard-coded.
"""
import os
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


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DEBUG", "False")

# SECURITY WARNING: keep the secret key used in production secret!
# In production the key MUST come from the environment. A weak fallback is only
# allowed for local development (DEBUG=True).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
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
    "crispy_forms",
    "crispy_tailwind",
    "apps.core.apps.CoreConfig",
    "apps.products.apps.ProductsConfig",
    "apps.cart.apps.CartConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.orders.apps.OrdersConfig",
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
            ],
        },
    },
]

WSGI_APPLICATION = "tileshop.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
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

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise for static file serving
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
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

# Limit upload size to blunt memory-exhaustion attacks (10 MB).
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Production-only protections (enabled automatically when DEBUG is off).
if not DEBUG:
    # The host (e.g. PythonAnywhere) terminates TLS and forwards this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True               # force HTTP -> HTTPS
    SESSION_COOKIE_SECURE = True             # cookies only over HTTPS
    CSRF_COOKIE_SECURE = True
    # HTTP Strict Transport Security — tell browsers "HTTPS only" for 1 year.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

"""
WSGI config for TileShop Premium project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tileshop.settings")
application = get_wsgi_application()

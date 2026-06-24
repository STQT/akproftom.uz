"""Passenger entry point for cPanel "Setup Python App".

cPanel's Passenger looks for a module-level ``application`` callable in this
file. We simply delegate to Django's WSGI application. The virtualenv created
by cPanel already puts the right Python on the path, so no sys.path hacks are
needed when the app root is this directory.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402

"""Development settings for PIN Platform."""
from .base import *  # noqa: F403,F401

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
INTERNAL_IPS = ["127.0.0.1"]

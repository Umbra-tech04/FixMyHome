"""Login throttling hooks for django-axes (see AXES_* in config/settings.py)."""

from django.conf import settings
from django.shortcuts import render


def normalize_username(request, credentials=None):
    """Lock out per e-mail address, case-insensitively, so "Anna@x.hu" and "anna@x.hu" share one counter."""
    field = settings.AXES_USERNAME_FORM_FIELD
    source = credentials if credentials else request.POST
    username = source.get(field) or ""
    return username.strip().lower()


def lockout_response(request, response=None, credentials=None, *args, **kwargs):
    """The same page for existing and unknown accounts, so it does not reveal whether an account exists."""
    minutes = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
    return render(request, "accounts/lockout.html", {"minutes": minutes}, status=429)

"""Shared shapes of database rules (CheckConstraint). The messages are what the admin and the model forms show
(violation_error_message) instead of an IntegrityError; the database enforces the rule for every other path
(queryset.update, bulk_create, shell, raw SQL, imports).

Every condition is NULL-safe on purpose: a CHECK passes when its condition is NULL, so nullable fields get an
explicit isnull branch, and config.migration_checks can find the breaking rows with exclude(condition).
"""

from django.db import models
from django.db.models import Q


def one_of(field, choices, name, message):
    return models.CheckConstraint(condition=Q(**{f"{field}__in": list(choices.values)}), name=name,
                                  violation_error_message=message)


def not_empty(field, name, message):
    return models.CheckConstraint(condition=~Q(**{field: ""}), name=name, violation_error_message=message)


def coordinate_constraints(prefix):
    """latitude/longitude: both empty or both given, and in range (degrees)."""
    return [
        models.CheckConstraint(
            condition=Q(latitude__isnull=True) | Q(latitude__gte=-90, latitude__lte=90),
            name=f"{prefix}_latitude_range",
            violation_error_message="A szélesség -90 és 90 fok között lehet.",
        ),
        models.CheckConstraint(
            condition=Q(longitude__isnull=True) | Q(longitude__gte=-180, longitude__lte=180),
            name=f"{prefix}_longitude_range",
            violation_error_message="A hosszúság -180 és 180 fok között lehet.",
        ),
        models.CheckConstraint(
            condition=Q(latitude__isnull=True, longitude__isnull=True)
            | Q(latitude__isnull=False, longitude__isnull=False),
            name=f"{prefix}_coordinates_together",
            violation_error_message="A szélességet és a hosszúságot együtt kell megadni (vagy egyiket sem).",
        ),
    ]

"""Checks that run in a migration before it adds a database rule (constraint).

If existing rows already break the rule, the migration stops with a readable message instead of a raw
IntegrityError, and it changes nothing: no row is deleted, merged or fixed. The rows have to be fixed by hand
(for example in the admin), then `python manage.py migrate` can run again.

Migrations call these with historical models (apps.get_model), so this module must not import app models.
"""

from django.core.management.base import CommandError
from django.db.models import Count
from django.db.models.functions import Lower

MAX_SHOWN = 20


class DataCheckError(CommandError):
    """Existing rows break a rule the migration is about to add. A CommandError, so `migrate` prints only the
    message, without a traceback."""


def check_constraints(apps, app_label, constraints_by_model):
    """Stop if any row breaks one of these CheckConstraints. constraints_by_model: {model name: [constraint]}."""
    problems = []
    for model_name, constraints in constraints_by_model.items():
        model = apps.get_model(app_label, model_name)
        for constraint in constraints:
            # CHECK passes when its condition is NULL; exclude() gives exactly the rows where it is FALSE,
            # because every condition here is written to be NULL-safe (explicit isnull branches).
            bad = model._default_manager.exclude(constraint.condition).order_by("pk")
            count = bad.count()
            if count:
                pks = ", ".join(f"#{pk}" for pk in bad.values_list("pk", flat=True)[:MAX_SHOWN])
                more = f" (és még {count - MAX_SHOWN})" if count > MAX_SHOWN else ""
                problems.append(
                    f"- {model._meta.verbose_name} ({constraint.name}): {constraint.violation_error_message} "
                    f"Sorok: {pks}{more}"
                )
    _fail_if(problems)


def check_case_insensitive_unique(apps, app_label, model_name, field):
    """Stop if two rows differ only in letter case in this field (as the database's own LOWER() sees it)."""
    model = apps.get_model(app_label, model_name)
    rows = model._default_manager.annotate(_key=Lower(field))
    keys = list(
        rows.values("_key").annotate(_n=Count("pk")).filter(_n__gt=1).order_by("_key").values_list("_key", flat=True)
    )
    problems = []
    for key in keys[:MAX_SHOWN]:
        same = ", ".join(f"#{pk} {value}" for pk, value in rows.filter(_key=key).order_by("pk").values_list("pk", field))
        problems.append(f"- {model._meta.verbose_name} {field}, csak kis/nagybetűben különbözik: {same}")
    if len(keys) > MAX_SHOWN:
        problems.append(f"- és még {len(keys) - MAX_SHOWN} ilyen csoport")
    _fail_if(problems)


def _fail_if(problems):
    if problems:
        raise DataCheckError(
            "A migráció leállt, és semmit nem változtatott: meglévő adatok sértik az új adatbázis-szabályokat.\n"
            + "\n".join(problems)
            + "\nJavítsd ezeket kézzel (pl. az adminban), majd futtasd újra: python manage.py migrate"
        )

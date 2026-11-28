"""seed_demo fits the database rules (accounts 0006, listings 0004) and can run more than once."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import MasterProfile, User
from listings.models import Ad, Application, Category, ServiceListing


class SeedDemoTests(TestCase):
    def seed(self):
        call_command("seed_demo", stdout=StringIO())

    def test_runs_twice_on_the_constrained_schema(self):
        self.seed()
        counts = [m.objects.count() for m in (User, MasterProfile, Ad, Application, ServiceListing)]
        self.seed()
        self.assertEqual([m.objects.count() for m in (User, MasterProfile, Ad, Application, ServiceListing)], counts)
        self.assertEqual(counts, [6, 4, 8, 3, 1])

    def test_every_seeded_row_passes_the_rule_checks(self):
        # The database already refused any breaking row; this also runs the same rules through Django's
        # validate_constraints, which the admin uses, so seeded rows can be edited and saved there.
        self.seed()
        for model in (User, MasterProfile, Ad, ServiceListing, Category):
            for obj in model.objects.all():
                with self.subTest(model=model.__name__, pk=obj.pk):
                    obj.validate_constraints()

"""Database rules on accounts: they hold even when save() and validation are bypassed.

Each IntegrityError test goes around the Python checks (queryset.update, bulk_create); the ValidationError
tests show the friendly message the admin and forms give instead.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import MasterProfile, Role, User
from listings.models import Category

PASSWORD = "Jelszo-12345"


def make_user(email="anna@example.com", **fields):
    return User.objects.create_user(email=email, password=PASSWORD, name="Anna", **fields)


class CaseInsensitiveEmailTests(TestCase):
    def setUp(self):
        self.anna = make_user("anna@example.com")

    def test_update_to_case_only_duplicate_is_rejected_by_the_database(self):
        bela = make_user("bela@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=bela.pk).update(email="ANNA@example.com")

    def test_bulk_create_of_case_only_duplicate_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="Anna@Example.com", name="Anna 2")])

    def test_different_addresses_are_allowed(self):
        User.objects.bulk_create([User(email="Bela@Example.com", name="Béla")])
        self.assertEqual(User.objects.count(), 2)

    def test_validate_constraints_gives_the_friendly_message(self):
        with self.assertRaises(ValidationError) as ctx:
            User(email="ANNA@example.com", name="Anna 2").validate_constraints()
        self.assertIn("Ezzel az e-mail-címmel már van fiók.", ctx.exception.messages)


class UserValueRuleTests(TestCase):
    def setUp(self):
        self.anna = make_user()

    def assert_db_refuses(self, **values):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=self.anna.pk).update(**values)

    def test_unknown_role_is_rejected_by_the_database(self):
        self.assert_db_refuses(role="admin")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="bela@example.com", name="Béla", role="boss")])

    def test_every_role_choice_is_allowed(self):
        for role in Role.values:
            User.objects.filter(pk=self.anna.pk).update(role=role)

    def test_empty_email_is_rejected_by_the_database(self):
        self.assert_db_refuses(email="")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="", name="Névtelen")])

    def test_friendly_messages(self):
        user = User(email="", name="Anna", role="boss")
        with self.assertRaises(ValidationError) as ctx:
            user.validate_constraints()
        self.assertIn("Érvénytelen szerepkör.", ctx.exception.messages)
        self.assertIn("Az e-mail-cím nem lehet üres.", ctx.exception.messages)


class MasterProfileCoordinateTests(TestCase):
    def setUp(self):
        self.profile = MasterProfile.objects.create(
            user=make_user("mester@example.com", role=Role.MASTER), profession=Category.objects.get(name="Vízszerelő"),
            service_area="Szabadka", contact="+381601234567", latitude=46.1, longitude=19.66,
        )

    def assert_db_refuses(self, **values):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MasterProfile.objects.filter(pk=self.profile.pk).update(**values)

    def test_out_of_range_coordinates_are_rejected_by_the_database(self):
        self.assert_db_refuses(latitude=90.5)
        self.assert_db_refuses(latitude=-91)
        self.assert_db_refuses(longitude=180.5)
        self.assert_db_refuses(longitude=-181)
        self.assert_db_refuses(latitude=float("inf"))

    def test_only_one_coordinate_is_rejected_by_the_database(self):
        self.assert_db_refuses(latitude=None)
        self.assert_db_refuses(longitude=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MasterProfile.objects.bulk_create([MasterProfile(
                user=make_user("masik@example.com", role=Role.MASTER), profession=self.profile.profession,
                service_area="Palics", contact="-", latitude=46.1,
            )])

    def test_edges_and_no_coordinates_are_allowed(self):
        MasterProfile.objects.filter(pk=self.profile.pk).update(latitude=90, longitude=-180)
        MasterProfile.objects.filter(pk=self.profile.pk).update(latitude=-90, longitude=180)
        MasterProfile.objects.filter(pk=self.profile.pk).update(latitude=None, longitude=None)

    def test_full_clean_gives_friendly_messages(self):
        self.profile.latitude, self.profile.longitude = 95, None
        with self.assertRaises(ValidationError) as ctx:
            self.profile.full_clean()
        self.assertIn("A szélesség -90 és 90 fok között lehet.", ctx.exception.messages)
        self.assertIn(
            "A szélességet és a hosszúságot együtt kell megadni (vagy egyiket sem).", ctx.exception.messages,
        )

    def test_admin_shows_the_message_instead_of_an_error_page(self):
        admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        self.client.force_login(admin)
        response = self.client.post(reverse("admin:accounts_masterprofile_change", args=[self.profile.pk]), {
            "user": self.profile.user_id, "profession": self.profile.profession_id, "service_area": "Szabadka",
            "contact": "+381601234567", "latitude": "46.1", "longitude": "200", "is_available": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A hosszúság -180 és 180 fok között lehet.")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.longitude, 19.66)

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from accounts.models import MasterProfile, Role
from listings.models import Ad, Application, Category, ServiceListing

User = get_user_model()


def make_user(email, role=Role.USER):
    return User.objects.create_user(email=email, password="Jelszo-12345", name=email.split("@")[0], role=role)


def make_ad(owner, category=None):
    category = category or Category.objects.get(name="Vízszerelő")
    return Ad.objects.create(
        owner=owner, title="Csöpög a csap", description="Folyik a konyhai csap.",
        category=category, location_text="Szabadka",
    )


class AdModelTests(TestCase):
    def test_ad_defaults_to_open(self):
        ad = make_ad(make_user("anna@example.com"))
        self.assertEqual(ad.status, Ad.Status.OPEN)

    def test_ad_coordinates_are_optional(self):
        ad = make_ad(make_user("anna@example.com"))
        self.assertIsNone(ad.latitude)
        self.assertIsNone(ad.longitude)

    def test_application_is_unique_per_ad_and_master(self):
        ad = make_ad(make_user("anna@example.com"))
        master = make_user("bela@example.com", Role.MASTER)
        Application.objects.create(ad=ad, master=master)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Application.objects.create(ad=ad, master=master)


class CategoryTests(TestCase):
    def test_seeded_categories_exist(self):
        self.assertTrue(Category.objects.filter(name="Vízszerelő").exists())
        self.assertGreaterEqual(Category.objects.count(), 6)

    def test_category_in_use_cannot_be_deleted(self):
        category = Category.objects.get(name="Festő")
        make_ad(make_user("anna@example.com"), category)
        with self.assertRaises(ProtectedError):
            category.delete()

    def test_category_used_by_master_profile_cannot_be_deleted(self):
        category = Category.objects.get(name="Hegesztő")
        MasterProfile.objects.create(
            user=make_user("bela@example.com", Role.MASTER), profession=category,
            service_area="Szabadka", contact="+381 60 000 000",
        )
        with self.assertRaises(ProtectedError):
            category.delete()


class ServiceListingTests(TestCase):
    def test_service_listing_requires_area_and_price_category(self):
        listing = ServiceListing(
            master=make_user("bela@example.com", Role.MASTER), title="Vízszerelés",
            description="Javítás, csere.", category=Category.objects.get(name="Vízszerelő"),
        )
        with self.assertRaises(ValidationError) as ctx:
            listing.full_clean()
        self.assertIn("service_area", ctx.exception.message_dict)
        self.assertIn("price_category", ctx.exception.message_dict)


class AdminTests(TestCase):
    def test_admin_changelist_loads_for_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="Jelszo-12345", name="Admin")
        self.client.force_login(admin)
        for model in ("category", "ad", "adimage", "application", "servicelisting"):
            response = self.client.get(reverse(f"admin:listings_{model}_changelist"))
            self.assertEqual(response.status_code, 200, model)
        response = self.client.get(reverse("admin:accounts_masterprofile_changelist"))
        self.assertEqual(response.status_code, 200)

"""Database rules on listings: they hold even when save() and validation are bypassed.

The IntegrityError tests go around the Python checks (queryset.update, bulk_create, create without full_clean);
the ValidationError and admin tests show the friendly message given instead.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from listings.models import Ad, Category, ServiceListing

PASSWORD = "Jelszo-12345"


def make_user(email, role=Role.USER):
    return User.objects.create_user(email=email, password=PASSWORD, name="Teszt Elek", role=role)


class AdRuleTests(TestCase):
    def setUp(self):
        self.owner = make_user("anna@example.com")
        self.master = make_user("mester@example.com", Role.MASTER)
        self.category = Category.objects.get(name="Vízszerelő")
        self.ad = Ad.objects.create(
            owner=self.owner, title="Csöpög a csap", description="Folyik a konyhai csap.", category=self.category,
            location_text="Szabadka", latitude=46.1, longitude=19.66,
        )

    def assert_db_refuses(self, **values):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ad.objects.filter(pk=self.ad.pk).update(**values)

    def new_ad(self, **fields):
        values = dict(owner=self.owner, title="Új", description="-", category=self.category, location_text="Palics")
        return Ad(**{**values, **fields})

    def test_out_of_range_or_half_coordinates_are_rejected_by_the_database(self):
        self.assert_db_refuses(latitude=91)
        self.assert_db_refuses(latitude=-90.01)
        self.assert_db_refuses(longitude=181)
        self.assert_db_refuses(longitude=float("-inf"))
        self.assert_db_refuses(latitude=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ad.objects.bulk_create([self.new_ad(longitude=19.7)])

    def test_unknown_status_is_rejected_by_the_database(self):
        self.assert_db_refuses(status="archived")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ad.objects.bulk_create([self.new_ad(status="")])

    def test_owner_cannot_be_the_chosen_master_in_the_database(self):
        self.assert_db_refuses(chosen_master=F("owner"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.new_ad(chosen_master=self.owner).save()  # plain save: no full_clean

    def test_empty_title_is_rejected_by_the_database(self):
        self.assert_db_refuses(title="")

    def test_allowed_values(self):
        for status in Ad.Status.values:
            Ad.objects.filter(pk=self.ad.pk).update(status=status)
        Ad.objects.filter(pk=self.ad.pk).update(chosen_master=self.master, latitude=None, longitude=None)

    def test_in_progress_without_chosen_master_is_still_allowed(self):
        # Deliberately no rule tying status to chosen_master: deleting a master's account empties chosen_master
        # (SET_NULL) on their in-progress jobs. Role and deletion rules are a team decision (PR 5).
        self.ad.choose(self.master)
        self.master.delete()
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.status, Ad.Status.IN_PROGRESS)
        self.assertIsNone(self.ad.chosen_master)

    def test_full_clean_gives_friendly_messages(self):
        ad = self.new_ad(chosen_master=self.owner, status="archived", title="", latitude=91)
        with self.assertRaises(ValidationError) as ctx:
            ad.full_clean(exclude=["title", "status"])  # field checks off: only the database rules speak
        messages = ctx.exception.messages
        self.assertIn("A hirdetés gazdája nem lehet a kiválasztott mester.", messages)
        self.assertIn("A szélesség -90 és 90 fok között lehet.", messages)
        self.assertIn("A szélességet és a hosszúságot együtt kell megadni (vagy egyiket sem).", messages)
        with self.assertRaises(ValidationError) as ctx:
            self.new_ad(status="archived", title="").validate_constraints()
        self.assertIn("Érvénytelen állapot.", ctx.exception.messages)
        self.assertIn("A cím nem lehet üres.", ctx.exception.messages)

    def test_admin_shows_the_message_instead_of_an_error_page(self):
        admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD, name="Admin")
        self.client.force_login(admin)
        response = self.client.post(reverse("admin:listings_ad_change", args=[self.ad.pk]), {
            "owner": self.owner.pk, "title": "Csöpög a csap", "description": "Folyik a konyhai csap.",
            "category": self.category.pk, "location_text": "Szabadka", "latitude": "46.1", "longitude": "19.66",
            "status": Ad.Status.IN_PROGRESS, "chosen_master": self.owner.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A hirdetés gazdája nem lehet a kiválasztott mester.")
        self.ad.refresh_from_db()
        self.assertIsNone(self.ad.chosen_master)


class ServiceListingRuleTests(TestCase):
    def setUp(self):
        self.service = ServiceListing.objects.create(
            master=make_user("mester@example.com", Role.MASTER), title="Csapcsere", description="-",
            category=Category.objects.get(name="Vízszerelő"), service_area="Szabadka",
            price_category=ServiceListing.PriceCategory.LOW,
        )

    def test_unknown_price_category_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ServiceListing.objects.filter(pk=self.service.pk).update(price_category="free")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ServiceListing.objects.filter(pk=self.service.pk).update(price_category="")

    def test_empty_title_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ServiceListing.objects.filter(pk=self.service.pk).update(title="")

    def test_friendly_messages(self):
        self.service.price_category, self.service.title = "free", ""
        with self.assertRaises(ValidationError) as ctx:
            self.service.validate_constraints()
        self.assertIn("Érvénytelen árkategória.", ctx.exception.messages)
        self.assertIn("A megnevezés nem lehet üres.", ctx.exception.messages)


class CategoryRuleTests(TestCase):
    def test_empty_name_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.bulk_create([Category(name="")])

    def test_friendly_message(self):
        with self.assertRaises(ValidationError) as ctx:
            Category(name="").validate_constraints()
        self.assertIn("A név nem lehet üres.", ctx.exception.messages)

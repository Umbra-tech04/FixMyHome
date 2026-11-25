from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import MasterProfile, Role
from listings.geo import CITIES, distance_km, nearby_masters
from listings.models import Ad, Application, Category, ServiceListing

User = get_user_model()


def make_user(email, role=Role.USER):
    return User.objects.create_user(email=email, password="Jelszo-12345", name=email.split("@")[0], role=role)


def make_master(email, profession="Vízszerelő", city="Szabadka", available=True):
    user = make_user(email, Role.MASTER)
    lat, lng = CITIES[city]
    MasterProfile.objects.create(
        user=user, profession=Category.objects.get(name=profession), service_area=city,
        contact="+381 60 000 000", latitude=lat, longitude=lng, is_available=available,
    )
    return user


def make_ad(owner, category="Vízszerelő", city="Szabadka", status=Ad.Status.OPEN):
    lat, lng = CITIES[city]
    return Ad.objects.create(
        owner=owner, title="Csöpög a csap", description="Folyik a konyhai csap.",
        category=Category.objects.get(name=category), location_text=city, latitude=lat, longitude=lng, status=status,
    )


class DistanceTests(SimpleTestCase):
    def test_szabadka_zenta_is_about_38_km(self):
        # A megadott koordinátákkal ennyi a valós légvonal (a brief 34 km-es becslése pontatlan volt).
        self.assertAlmostEqual(distance_km(*CITIES["Szabadka"], *CITIES["Zenta"]), 38, delta=2)

    def test_same_point_is_zero(self):
        self.assertEqual(distance_km(*CITIES["Szabadka"], *CITIES["Szabadka"]), 0)


class NearbyMastersTests(TestCase):
    def test_only_available_masters_sorted_by_distance(self):
        make_master("palics@example.com", city="Palics")
        make_master("szabadka@example.com", city="Szabadka")
        make_master("szunetel@example.com", city="Szabadka", available=False)
        names = [p.user.email for p in nearby_masters(*CITIES["Szabadka"], 20)]
        self.assertEqual(names, ["szabadka@example.com", "palics@example.com"])

    def test_api_suggests_bigger_radius_when_empty(self):
        make_master("zenta@example.com", city="Zenta")
        self.client.force_login(make_user("anna@example.com"))
        lat, lng = CITIES["Szabadka"]
        data = self.client.get(reverse("listings:api_masters"), {"lat": lat, "lng": lng, "r": 10}).json()
        self.assertEqual(data["masters"], [])
        self.assertEqual(data["suggest_radius"], 50)


class ApplicationFlowTests(TestCase):
    def setUp(self):
        self.owner = make_user("anna@example.com")
        self.ad = make_ad(self.owner)
        self.master = make_master("bela@example.com")

    def test_double_application_is_rejected(self):
        self.client.force_login(self.master)
        url = reverse("listings:apply", args=[self.ad.pk])
        self.client.post(url, {"message": "Holnap ráérek."})
        self.client.post(url, {"message": "Még egyszer."})
        self.assertEqual(Application.objects.filter(ad=self.ad, master=self.master).count(), 1)

    def test_cannot_apply_to_closed_ad(self):
        self.ad.status = Ad.Status.DONE
        self.ad.save()
        self.client.force_login(self.master)
        self.client.post(reverse("listings:apply", args=[self.ad.pk]), {"message": ""})
        self.assertFalse(Application.objects.exists())

    def test_choosing_accepts_one_rejects_others_and_starts_work(self):
        other = make_master("csaba@example.com")
        chosen_app = Application.objects.create(ad=self.ad, master=self.master)
        other_app = Application.objects.create(ad=self.ad, master=other)
        self.assertEqual(chosen_app.status, "pending")
        self.client.force_login(self.owner)
        self.client.post(reverse("listings:choose_master", args=[self.ad.pk, chosen_app.pk]))
        self.ad.refresh_from_db()
        chosen_app.refresh_from_db()
        other_app.refresh_from_db()
        self.assertEqual(self.ad.status, Ad.Status.IN_PROGRESS)
        self.assertEqual(chosen_app.status, "accepted")
        self.assertEqual(other_app.status, "rejected")

    def test_only_owner_can_choose(self):
        application = Application.objects.create(ad=self.ad, master=self.master)
        self.client.force_login(make_user("mas@example.com"))
        response = self.client.post(reverse("listings:choose_master", args=[self.ad.pk, application.pk]))
        self.assertEqual(response.status_code, 404)

    def test_my_jobs_lists_accepted_ads_with_filter(self):
        self.ad.choose(self.master)
        self.client.force_login(self.master)
        self.assertContains(self.client.get(reverse("listings:my_jobs"), {"allapot": "in_progress"}), self.ad.title)
        self.assertNotContains(self.client.get(reverse("listings:my_jobs"), {"allapot": "closed"}), self.ad.title)


class AdTransitionTests(TestCase):
    def setUp(self):
        self.ad = make_ad(make_user("anna@example.com"))

    def test_closed_ad_cannot_reopen(self):
        self.ad.status = Ad.Status.DONE
        self.assertFalse(self.ad.can_transition_to(Ad.Status.OPEN))
        with self.assertRaises(ValidationError):
            self.ad.transition_to(Ad.Status.OPEN)

    def test_only_forward(self):
        self.assertTrue(self.ad.can_transition_to(Ad.Status.IN_PROGRESS))
        self.assertTrue(self.ad.can_transition_to(Ad.Status.WITHDRAWN))
        self.assertFalse(self.ad.can_transition_to(Ad.Status.DONE))

    def test_owner_can_withdraw_via_view(self):
        self.client.force_login(self.ad.owner)
        self.client.post(reverse("listings:ad_set_status", args=[self.ad.pk]), {"status": "withdrawn"})
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.status, Ad.Status.WITHDRAWN)


class FormAndRoleTests(TestCase):
    def test_ad_create_uses_city_coordinates_and_shows_field_errors(self):
        self.client.force_login(make_user("anna@example.com"))
        url = reverse("listings:ad_create")
        response = self.client.post(url, {"title": "", "description": "x", "location_text": "Atlantisz"})
        self.assertContains(response, 'has-error')
        self.assertContains(response, 'class="field-error"')
        self.assertContains(response, "Ismeretlen település")
        category = Category.objects.get(name="Festő")
        self.client.post(url, {"title": "Festés", "description": "Két szoba.", "category": category.pk, "location_text": "zenta"})
        ad = Ad.objects.get(title="Festés")
        self.assertEqual((ad.latitude, ad.longitude), CITIES["Zenta"])
        self.assertEqual(ad.status, Ad.Status.OPEN)

    def test_user_cannot_open_master_pages(self):
        self.client.force_login(make_user("anna@example.com"))
        for name in ("master_ads", "my_jobs", "service_list", "master_profile"):
            self.assertEqual(self.client.get(reverse(f"listings:{name}")).status_code, 403, name)

    def test_master_sees_only_matching_nearby_ads(self):
        owner = make_user("anna@example.com")
        near = make_ad(owner, "Vízszerelő", "Palics")
        make_ad(owner, "Festő", "Szabadka")
        far = make_ad(owner, "Vízszerelő", "Újvidék")
        self.client.force_login(make_master("bela@example.com"))
        ads = list(self.client.get(reverse("listings:master_ads")).context["ads"])
        self.assertEqual(ads, [near])
        self.assertNotIn(far, ads)


class ServiceCrudTests(TestCase):
    def setUp(self):
        self.master = make_master("bela@example.com")
        self.service = ServiceListing.objects.create(
            master=self.master, title="Csapcsere", description="Gyorsan.", category=Category.objects.get(name="Vízszerelő"),
            service_area="Szabadka", price_category=ServiceListing.PriceCategory.LOW,
        )

    def test_pause_and_delete_own_service(self):
        self.client.force_login(self.master)
        self.client.post(reverse("listings:service_toggle", args=[self.service.pk]))
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)
        self.assertContains(self.client.get(reverse("listings:service_delete", args=[self.service.pk])), "Biztosan törlöd")
        self.client.post(reverse("listings:service_delete", args=[self.service.pk]))
        self.assertFalse(ServiceListing.objects.exists())

    def test_cannot_touch_others_service(self):
        self.client.force_login(make_master("csaba@example.com"))
        self.assertEqual(self.client.post(reverse("listings:service_delete", args=[self.service.pk])).status_code, 404)
        self.assertTrue(ServiceListing.objects.exists())


class LocationLookupTests(TestCase):
    def test_city_lookup_accepts_zip_and_free_text(self):
        from listings.geo import city_coords
        self.assertEqual(city_coords("24000"), CITIES["Szabadka"])
        self.assertEqual(city_coords("Szabadka és környéke"), CITIES["Szabadka"])
        self.assertIsNone(city_coords("Atlantisz"))

    def test_registered_master_without_coordinates_is_found_by_service_area(self):
        user = make_user("uj@example.com", Role.MASTER)
        MasterProfile.objects.create(
            user=user, profession=Category.objects.get(name="Festő"), service_area="Palics és környéke", contact="x",
        )
        self.assertEqual([p.user for p in nearby_masters(*CITIES["Szabadka"], 10)], [user])


class DemoFlowEndToEndTests(TestCase):
    """A bemutató fő útja egyben: hirdetés → jelentkezés → kiválasztás → Munkáim."""

    def test_full_demo_flow(self):
        customer = User.objects.create_user(email="anna@example.com", password="Jelszo-12345", name="Anna", role=Role.USER)
        electrician = make_master("peter@example.com", profession="Villanyszerelő", city="Szabadka")
        rival = make_master("gabor@example.com", profession="Villanyszerelő", city="Palics")
        villany = Category.objects.get(name="Villanyszerelő")

        # 1) A felhasználó belép, és hirdetést ad fel.
        response = self.client.post(reverse("login"), {"username": "anna@example.com", "password": "Jelszo-12345"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse("listings:ad_create"), {
            "title": "Nincs áram a konyhában", "description": "Lecsap a biztosíték.",
            "category": villany.pk, "location_text": "Szabadka",
        })
        ad = Ad.objects.get(title="Nincs áram a konyhában")
        self.assertRedirects(response, reverse("listings:ad_detail", args=[ad.pk]))
        self.assertEqual(ad.status, Ad.Status.OPEN)

        # 2) A villanyszerelő látja a környékbeli hirdetések között, és jelentkezik.
        self.client.force_login(electrician)
        self.assertContains(self.client.get(reverse("listings:master_ads")), "Nincs áram a konyhában")
        self.client.post(reverse("listings:apply", args=[ad.pk]), {"message": "Ma délután ráérek."})
        self.client.force_login(rival)
        self.client.post(reverse("listings:apply", args=[ad.pk]), {"message": "Holnap mehetek."})
        self.assertEqual(ad.applications.count(), 2)

        # 3) A felhasználó látja a jelentkezőket, és kiválasztja a villanyszerelőt.
        self.client.force_login(customer)
        detail = self.client.get(reverse("listings:ad_detail", args=[ad.pk]))
        self.assertContains(detail, "Ma délután ráérek.")
        self.assertContains(detail, "Függőben")
        chosen = ad.applications.get(master=electrician)
        self.client.post(reverse("listings:choose_master", args=[ad.pk, chosen.pk]))
        ad.refresh_from_db()
        self.assertEqual(ad.status, Ad.Status.IN_PROGRESS)
        self.assertEqual(ad.chosen_master, electrician)
        self.assertEqual(ad.applications.get(master=rival).status, "rejected")
        self.assertContains(self.client.get(reverse("listings:ad_detail", args=[ad.pk])), "Elutasítva")

        # 4) A munka megjelenik a mester Munkáim oldalán; új jelentkezés már nem fogadható.
        self.client.force_login(electrician)
        self.assertContains(self.client.get(reverse("listings:my_jobs")), "Nincs áram a konyhában")
        late = make_master("kesve@example.com", profession="Villanyszerelő")
        self.client.force_login(late)
        self.client.post(reverse("listings:apply", args=[ad.pk]), {"message": "Én is mennék."})
        self.assertFalse(ad.applications.filter(master=late).exists())

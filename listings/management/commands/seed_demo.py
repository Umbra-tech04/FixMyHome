from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import MasterProfile, Role, User
from listings.geo import CITIES
from listings.models import Ad, Category, ServiceListing

PASSWORD = "test1234"
CATEGORIES = ["Villanyszerelő", "Vízszerelő", "Festő", "Asztalos", "Burkoló", "Lakatos"]

# (e-mail, név, szakma, település, elérhető)
MASTERS = [
    ("villanyszerelo@fixmyhome.test", "Kovács Péter", "Villanyszerelő", "Szabadka", True),
    ("vizszerelo@fixmyhome.test", "Nagy István", "Vízszerelő", "Palics", True),
    ("festo@fixmyhome.test", "Szabó Anna", "Festő", "Topolya", True),
    ("asztalos@fixmyhome.test", "Tóth Gábor", "Asztalos", "Zenta", False),
]

# (cím, leírás, kategória, település)
ADS = [
    ("Csöpög a konyhai csap", "Napok óta csöpög a csap, a tömítést kellene cserélni.", "Vízszerelő", "Szabadka"),
    ("Nem működik a konnektor", "A nappaliban két konnektor nem ad áramot, a biztosíték rendben van.", "Villanyszerelő", "Szabadka"),
    ("Szobafestés, 2 szoba", "Két kb. 15 m²-es szoba festése, a bútorokat kipakoljuk.", "Festő", "Szabadka"),
]


class Command(BaseCommand):
    help = "Bemutató adatok: tesztfiókok (jelszó: test1234), mesterek, nyitott hirdetések, egy szolgáltatás. Többször futtatható."

    def account(self, email, name, role, phone=""):
        user, _ = User.objects.update_or_create(email=email, defaults={"name": name, "role": role, "phone": phone})
        user.set_password(PASSWORD)
        user.save()
        return user

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {name: Category.objects.get_or_create(name=name)[0] for name in CATEGORIES}

        customer = self.account("felhasznalo@fixmyhome.test", "Teszt Felhasználó", Role.USER, "+381 60 100 0001")
        self.account("ugyfelszolgalat@fixmyhome.test", "Ügyfélszolgálat", Role.SUPPORT)

        masters = {}
        for i, (email, name, profession, city, available) in enumerate(MASTERS, start=1):
            phone = f"+381 60 200 000{i}"
            user = self.account(email, name, Role.MASTER, phone)
            lat, lng = CITIES[city]
            MasterProfile.objects.update_or_create(user=user, defaults={
                "profession": categories[profession], "service_area": city, "contact": phone,
                "latitude": lat, "longitude": lng, "is_available": available,
            })
            masters[profession] = user

        for title, description, category, city in ADS:
            lat, lng = CITIES[city]
            Ad.objects.get_or_create(owner=customer, title=title, defaults={
                "description": description, "category": categories[category],
                "location_text": city, "latitude": lat, "longitude": lng,
            })

        ServiceListing.objects.get_or_create(master=masters["Villanyszerelő"], title="Villanyszerelés, hibaelhárítás", defaults={
            "description": "Konnektorok, kapcsolók, lámpák szerelése; hibakeresés 24 órán belül.",
            "category": categories["Villanyszerelő"], "service_area": "Szabadka és környéke",
            "price_category": ServiceListing.PriceCategory.MEDIUM,
        })

        self.stdout.write(self.style.SUCCESS(f"Kész. Tesztfiókok jelszava: {PASSWORD}"))

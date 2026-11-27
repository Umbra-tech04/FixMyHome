from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import MasterProfile, Role, User
from listings.geo import CITIES
from listings.models import Ad, Application, Category, ServiceListing

PASSWORD = "test1234"
CATEGORIES = ["Villanyszerelő", "Vízszerelő", "Festő", "Asztalos", "Burkoló", "Lakatos"]

# (e-mail, név, szakma, település, elérhető)
MASTERS = [
    ("villanyszerelo@fixmyhome.test", "Kovács Péter", "Villanyszerelő", "Szabadka", True),
    ("vizszerelo@fixmyhome.test", "Nagy István", "Vízszerelő", "Palics", True),
    ("festo@fixmyhome.test", "Szabó Anna", "Festő", "Topolya", True),
    ("asztalos@fixmyhome.test", "Tóth Gábor", "Asztalos", "Zenta", False),
]

OPEN, IN_PROGRESS, DONE = Ad.Status.OPEN, Ad.Status.IN_PROGRESS, Ad.Status.DONE

# (cím, leírás, kategória, település, állapot, kiválasztott mester szakmája)
ADS = [
    ("Csöpög a konyhai csap", "Napok óta csöpög a csap, a tömítést kellene cserélni.", "Vízszerelő", "Szabadka", OPEN, None),
    ("Nem működik a konnektor", "A nappaliban két konnektor nem ad áramot, a biztosíték rendben van.", "Villanyszerelő", "Szabadka", OPEN, None),
    ("Szobafestés, 2 szoba", "Két kb. 15 m²-es szoba festése, a bútorokat kipakoljuk.", "Festő", "Szabadka", OPEN, None),
    ("Csillár felszerelése a nappaliba", "Megvan a lámpa, csak fel kellene szerelni. 2,8 m a belmagasság.", "Villanyszerelő", "Palics", OPEN, None),
    ("Fürdőszoba csempézése", "Kb. 12 m² falburkolat, a csempét már megvettük.", "Burkoló", "Szabadka", OPEN, None),
    ("Zárcsere a bejárati ajtón", "Akad a zár, új hengerbetét kellene, lehetőleg még a héten.", "Lakatos", "Palics", OPEN, None),
    ("Kiégett a konyhai biztosíték", "Tegnap óta a konyhában egyik konnektor sem működik, a biztosíték mindig lecsap.", "Villanyszerelő", "Szabadka", IN_PROGRESS, "Villanyszerelő"),
    ("Villanyóra-szekrény cseréje", "Régi, rozsdás mérőszekrény cseréje az előírások szerint.", "Villanyszerelő", "Szabadka", DONE, "Villanyszerelő"),
]

# (hirdetés címe, mester szakmája, üzenet): a Hirdetéseim és a Munkáim ne legyen üres
APPLICATIONS = [
    ("Csöpög a konyhai csap", "Vízszerelő", "Holnap délelőtt ki tudok menni, a tömítés nálam van."),
    ("Kiégett a konyhai biztosíték", "Villanyszerelő", "Ma délután ráérek, hozom a műszert is."),
    ("Villanyóra-szekrény cseréje", "Villanyszerelő", "Vállalom, az anyagot is beszerzem."),
]


class Command(BaseCommand):
    help = "Bemutató adatok: tesztfiókok (jelszó: test1234), mesterek, hirdetések, jelentkezések, egy szolgáltatás. Többször futtatható."

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

        ads = {}
        for title, description, category, city, status, chosen in ADS:
            lat, lng = CITIES[city]
            ads[title], _ = Ad.objects.get_or_create(owner=customer, title=title, defaults={
                "description": description, "category": categories[category],
                "location_text": city, "latitude": lat, "longitude": lng,
                "status": status, "chosen_master": masters[chosen] if chosen else None,
            })

        for title, profession, message in APPLICATIONS:
            Application.objects.get_or_create(ad=ads[title], master=masters[profession], defaults={"message": message})

        ServiceListing.objects.get_or_create(master=masters["Villanyszerelő"], title="Villanyszerelés, hibaelhárítás", defaults={
            "description": "Konnektorok, kapcsolók, lámpák szerelése; hibakeresés 24 órán belül.",
            "category": categories["Villanyszerelő"], "service_area": "Szabadka és környéke",
            "price_category": ServiceListing.PriceCategory.MEDIUM,
        })

        self.stdout.write(self.style.SUCCESS(f"Kész. Tesztfiókok jelszava: {PASSWORD}"))

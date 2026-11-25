from math import asin, ceil, cos, radians, sin, sqrt

from accounts.models import MasterProfile
from listings.models import Ad

# Vajdasági települések: ha a böngésző nem ad koordinátát, ebből számolunk.
CITIES = {
    "Szabadka": (46.1003, 19.6656),
    "Palics": (46.1000, 19.7667),
    "Zenta": (45.9275, 20.0900),
    "Topolya": (45.8156, 19.6347),
    "Magyarkanizsa": (46.0667, 20.0500),
    "Óbecse": (45.6167, 20.0500),
    "Zombor": (45.7733, 19.1122),
    "Újvidék": (45.2671, 19.8335),
}
_CITIES_LOWER = {name.lower(): coords for name, coords in CITIES.items()}

RADIUS_STEPS = (5, 10, 20, 50, 100)
EARTH_RADIUS_KM = 6371.0088


def city_coords(name):
    return _CITIES_LOWER.get((name or "").strip().lower())


def distance_km(lat1, lng1, lat2, lng2):
    """Haversine-távolság két pont között, kilométerben."""
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def _within(objects, lat, lng, radius_km):
    # TODO(shortcut): a távolságot Pythonban számoljuk minden sorra, ez pár száz rekordig jó; ha több ezer lesz, kell egy bounding-box szűrés a lekérdezésben (vagy PostGIS).
    result = []
    for obj in objects:
        obj.distance = distance_km(lat, lng, obj.latitude, obj.longitude)
        if radius_km is None or obj.distance <= radius_km:
            result.append(obj)
    return sorted(result, key=lambda obj: obj.distance)


def nearby_masters(lat, lng, radius_km=None):
    """Az elérhető mesterek profiljai a körzeten belül, a legközelebbi elöl (`.distance` km-ben)."""
    profiles = MasterProfile.objects.filter(
        is_available=True, user__is_active=True, latitude__isnull=False, longitude__isnull=False,
    ).select_related("user", "profession")
    return _within(profiles, lat, lng, radius_km)


def nearby_open_ads(lat, lng, radius_km, category):
    ads = Ad.objects.filter(
        status=Ad.Status.OPEN, category=category, latitude__isnull=False, longitude__isnull=False,
    ).select_related("category")
    return _within(ads, lat, lng, radius_km)


def suggest_radius(lat, lng, radius_km):
    """Üres találatnál: a legkisebb körzetlépcső, amelyben már van elérhető mester (vagy None)."""
    masters = nearby_masters(lat, lng)
    if not masters:
        return None
    nearest = masters[0].distance
    return next((step for step in RADIUS_STEPS if step > radius_km and step >= nearest), ceil(nearest))

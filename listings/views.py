from math import isfinite

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import MasterProfile, Role
from accounts.permissions import role_required
from listings import geo
from listings.forms import AdForm, ApplicationForm, LocationForm, MasterProfileForm, ServiceListingForm
from listings.models import Ad, Application, Category, ServiceListing


def _radius(request, default):
    try:
        radius = float(request.GET.get("r", default))
    except (TypeError, ValueError):
        return default
    return min(max(radius, 1), 200) if isfinite(radius) else default


def _session_location(request):
    """A felhasználó helye a sessionben: {"lat", "lng", "text"} vagy None."""
    return request.session.get("location")


# --- Felhasználó: hirdetések -------------------------------------------------------------------

@role_required(Role.USER)
def ad_create(request):
    form = AdForm(request.POST or None, request.FILES or None, initial={"category": request.GET.get("kat")})
    if request.method == "POST" and form.is_valid():
        form.instance.owner = request.user
        ad = form.save()
        messages.success(request, "A hirdetésed megjelent.")
        return redirect("listings:ad_detail", pk=ad.pk)
    return render(request, "listings/ad_form.html", {"form": form, "cities": geo.CITIES})


@role_required(Role.USER)
def ad_edit(request, pk):
    ad = get_object_or_404(Ad, pk=pk, owner=request.user)
    if not ad.is_editable:
        messages.error(request, "Lezárt vagy visszavont hirdetés nem szerkeszthető.")
        return redirect("listings:ad_detail", pk=ad.pk)
    form = AdForm(request.POST or None, request.FILES or None, instance=ad)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "A hirdetés módosítva.")
        return redirect("listings:ad_detail", pk=ad.pk)
    return render(request, "listings/ad_form.html", {"form": form, "ad": ad, "cities": geo.CITIES})


@role_required(Role.USER)
def my_ads(request):
    ads = Ad.objects.filter(owner=request.user).select_related("category").annotate(application_count=Count("applications"))
    return render(request, "listings/my_ads.html", {"ads": ads})


@role_required(Role.USER)
@require_POST
def ad_set_status(request, pk):
    ad = get_object_or_404(Ad, pk=pk, owner=request.user)
    target = request.POST.get("status")
    # A Folyamatban állapotba csak mester kiválasztásával lehet lépni (choose_master).
    if target not in (Ad.Status.WITHDRAWN, Ad.Status.DONE):
        messages.error(request, "Ismeretlen állapot.")
        return redirect("listings:ad_detail", pk=ad.pk)
    try:
        ad.transition_to(target)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        ad.save(update_fields=["status"])
        messages.success(request, f"A hirdetés állapota: {ad.get_status_display()}.")
    return redirect("listings:ad_detail", pk=ad.pk)


@role_required(Role.USER)
@require_POST
def choose_master(request, pk, application_pk):
    ad = get_object_or_404(Ad, pk=pk, owner=request.user)
    application = get_object_or_404(Application.objects.select_related("master"), pk=application_pk, ad=ad)
    try:
        ad.choose(application.master)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        messages.success(request, f"Kiválasztottad: {application.master.name}.")
    return redirect("listings:ad_detail", pk=ad.pk)


# --- Hirdetés részlete és jelentkezés ------------------------------------------------------------

def _render_ad_detail(request, ad, application_form=None, status=200):
    user = request.user
    context = {"ad": ad, "images": ad.images.all()}
    if user == ad.owner:
        context.update(
            applications=ad.applications.select_related("master__master_profile__profession"),
            can_withdraw=ad.can_transition_to(Ad.Status.WITHDRAWN),
            can_close=ad.can_transition_to(Ad.Status.DONE),
        )
    elif user.role == Role.MASTER:
        profile = MasterProfile.objects.filter(user=user).first()
        if profile and None not in (profile.latitude, profile.longitude, ad.latitude, ad.longitude):
            context["distance"] = geo.distance_km(profile.latitude, profile.longitude, ad.latitude, ad.longitude)
        context.update(
            my_application=ad.applications.filter(master=user).first(),
            application_form=application_form or ApplicationForm(),
        )
    return render(request, "listings/ad_detail.html", context, status=status)


@login_required
def ad_detail(request, pk):
    ad = get_object_or_404(Ad.objects.select_related("owner", "category", "chosen_master"), pk=pk)
    if request.user != ad.owner and request.user.role not in (Role.MASTER, Role.SUPPORT):
        raise PermissionDenied
    return _render_ad_detail(request, ad)


@role_required(Role.MASTER)
@require_POST
def apply(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if not ad.accepts_applications:
        messages.error(request, "Erre a hirdetésre már nem lehet jelentkezni.")
        return redirect("listings:ad_detail", pk=ad.pk)
    if ad.applications.filter(master=request.user).exists():
        messages.error(request, "Erre a hirdetésre már jelentkeztél.")
        return redirect("listings:ad_detail", pk=ad.pk)
    form = ApplicationForm(request.POST)
    if not form.is_valid():
        return _render_ad_detail(request, ad, application_form=form, status=400)
    try:
        with transaction.atomic():
            Application.objects.create(ad=ad, master=request.user, message=form.cleaned_data["message"])
    except IntegrityError:  # párhuzamos dupla kattintás
        messages.error(request, "Erre a hirdetésre már jelentkeztél.")
    else:
        messages.success(request, "Jelentkeztél a hirdetésre.")
    return redirect("listings:ad_detail", pk=ad.pk)


@role_required(Role.MASTER)
@require_POST
def withdraw_application(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if not ad.accepts_applications:
        messages.error(request, "A jelentkezés már nem vonható vissza.")
    elif ad.applications.filter(master=request.user).delete()[0]:
        messages.success(request, "Visszavontad a jelentkezésed.")
    return redirect("listings:ad_detail", pk=ad.pk)


# --- Felhasználó: hely és közeli mesterek ------------------------------------------------------

def _nearby_masters_page(request, location_form=None, status=200):
    location = _session_location(request)
    radius = _radius(request, 10)
    category = request.GET.get("kat") or None
    masters = suggestion = None
    if location:
        masters = geo.nearby_masters(location["lat"], location["lng"], radius)
        if category:
            masters = [p for p in masters if p.profession.name == category]
        if not masters:
            suggestion = geo.suggest_radius(location["lat"], location["lng"], radius)
    form = location_form or LocationForm(initial={"location_text": (location or {}).get("text", "")})
    return render(request, "listings/nearby_masters.html", {
        "location": location, "radius": radius, "radius_choices": (5, 10, 20),
        "masters": masters, "suggestion": suggestion, "location_form": form, "cities": geo.CITIES,
        "categories": Category.objects.all(), "category": category,
    }, status=status)


@role_required(Role.USER)
def nearby_masters(request):
    return _nearby_masters_page(request)


@role_required(Role.USER)
@require_POST
def save_location(request):
    form = LocationForm(request.POST)
    if not form.is_valid():
        return _nearby_masters_page(request, location_form=form, status=400)
    data = form.cleaned_data
    request.session["location"] = {
        "lat": data["latitude"], "lng": data["longitude"], "text": data["location_text"].strip(),
    }
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
        return redirect(next_url)
    return redirect("listings:nearby_masters")


@role_required(Role.USER)
def api_masters(request):
    location = _session_location(request) or {}
    try:
        lat = float(request.GET.get("lat", location.get("lat")))
        lng = float(request.GET.get("lng", location.get("lng")))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Adj meg érvényes lat és lng paramétert."}, status=400)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return JsonResponse({"error": "A koordináták a megengedett tartományon kívül esnek."}, status=400)
    radius = _radius(request, 10)
    masters = geo.nearby_masters(lat, lng, radius)
    return JsonResponse({
        "radius_km": radius,
        "masters": [{
            "id": p.user_id, "name": p.user.name, "profession": p.profession.name, "city": p.service_area,
            "distance_km": round(p.distance, 1), "lat": p.latitude, "lng": p.longitude,
        } for p in masters],
        "suggest_radius": None if masters else geo.suggest_radius(lat, lng, radius),
    })


# --- Mester -------------------------------------------------------------------------------------

@role_required(Role.MASTER)
def master_profile(request):
    profile = MasterProfile.objects.filter(user=request.user).first() or MasterProfile(user=request.user)
    form = MasterProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Az adataid elmentve.")
        return redirect("listings:master_profile")
    return render(request, "listings/master_profile.html", {"form": form, "cities": geo.CITIES})


@role_required(Role.MASTER)
def master_ads(request):
    profile = MasterProfile.objects.filter(user=request.user).select_related("profession").first()
    radius = _radius(request, 20)
    ads = None
    if profile and profile.latitude is not None and profile.longitude is not None:
        ads = geo.nearby_open_ads(profile.latitude, profile.longitude, radius, profile.profession)
    return render(request, "listings/master_ads.html", {
        "profile": profile, "ads": ads, "radius": radius, "radius_choices": (10, 20, 50),
        "applied_ids": set(Application.objects.filter(master=request.user).values_list("ad_id", flat=True)),
    })


JOB_FILTERS = {
    "in_progress": ("Folyamatban", [Ad.Status.IN_PROGRESS]),
    "closed": ("Lezárva", [Ad.Status.DONE]),
    "all": ("Mind", None),
}


@role_required(Role.MASTER)
def my_jobs(request):
    selected = request.GET.get("allapot", "in_progress")
    if selected not in JOB_FILTERS:
        selected = "in_progress"
    jobs = Ad.objects.filter(chosen_master=request.user).select_related("owner", "category")
    statuses = JOB_FILTERS[selected][1]
    if statuses:
        jobs = jobs.filter(status__in=statuses)
    filters = [(key, label) for key, (label, _) in JOB_FILTERS.items()]
    return render(request, "listings/my_jobs.html", {"jobs": jobs, "selected": selected, "filters": filters})


@role_required(Role.MASTER)
def service_list(request):
    services = ServiceListing.objects.filter(master=request.user).select_related("category")
    return render(request, "listings/service_list.html", {"services": services})


@role_required(Role.MASTER)
def service_form(request, pk=None):
    service = get_object_or_404(ServiceListing, pk=pk, master=request.user) if pk else ServiceListing(master=request.user)
    form = ServiceListingForm(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "A szolgáltatás elmentve.")
        return redirect("listings:service_list")
    return render(request, "listings/service_form.html", {"form": form, "service": service, "cities": geo.CITIES})


@role_required(Role.MASTER)
@require_POST
def service_toggle(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk, master=request.user)
    service.is_active = not service.is_active
    service.save(update_fields=["is_active"])
    messages.success(request, "A szolgáltatás újra aktív." if service.is_active else "A szolgáltatás szüneteltetve.")
    return redirect("listings:service_list")


@role_required(Role.MASTER)
def service_delete(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk, master=request.user)
    if request.method == "POST":
        service.delete()
        messages.success(request, "A szolgáltatás törölve.")
        return redirect("listings:service_list")
    return render(request, "listings/service_confirm_delete.html", {"service": service})

from django import forms
from django.db import transaction

from accounts.models import MasterProfile
from listings.geo import city_coords
from listings.models import Ad, AdImage, Application, ServiceListing

CITY_INPUT = forms.TextInput(attrs={"list": "cities", "autocomplete": "off"})
MAX_IMAGES = 10


def fill_coords(form, text_field):
    """A böngészőből jövő rejtett lat/lng nyer; ha nincs, a település koordinátája a CITIES-táblából."""
    data = form.cleaned_data
    lat, lng = data.get("latitude"), data.get("longitude")
    coords_given = lat is not None and lng is not None
    # Szerkesztéskor a régi rejtett koordináták maradnának, ha csak a település változott.
    if text_field in form.changed_data and not {"latitude", "longitude"} & set(form.changed_data):
        coords_given = False
    if coords_given:
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            form.add_error(text_field, "Érvénytelen koordináták.")
        return
    coords = city_coords(data.get(text_field))
    if coords:
        data["latitude"], data["longitude"] = coords
    elif text_field not in form.errors:
        form.add_error(text_field, "Ismeretlen település: válassz a listából, vagy engedélyezd a helymeghatározást.")


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleImageInput(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data] if data else []
        if len(files) > MAX_IMAGES:
            raise forms.ValidationError(f"Legfeljebb {MAX_IMAGES} képet tölthetsz fel.")
        return [super(MultipleImageField, self).clean(f, initial) for f in files]


class AdForm(forms.ModelForm):
    images = MultipleImageField(label="Képek", required=False)

    class Meta:
        model = Ad
        fields = ["title", "description", "category", "location_text", "latitude", "longitude"]
        labels = {"title": "Cím", "description": "Leírás", "category": "Kategória", "location_text": "Település"}
        widgets = {"location_text": CITY_INPUT, "latitude": forms.HiddenInput(), "longitude": forms.HiddenInput()}

    def clean(self):
        cleaned = super().clean()
        fill_coords(self, "location_text")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        ad = super().save()
        for image in self.cleaned_data["images"]:
            AdImage.objects.create(ad=ad, image=image)
        return ad


class MasterProfileForm(forms.ModelForm):
    class Meta:
        model = MasterProfile
        fields = ["profession", "service_area", "contact", "latitude", "longitude", "is_available"]
        labels = {
            "profession": "Szakma", "service_area": "Település", "contact": "Elérhetőség",
            "is_available": "Most elérhető vagyok",
        }
        widgets = {
            "service_area": CITY_INPUT, "latitude": forms.HiddenInput(), "longitude": forms.HiddenInput(),
            "is_available": forms.CheckboxInput(attrs={"class": "toggle"}),
        }

    def clean(self):
        cleaned = super().clean()
        fill_coords(self, "service_area")
        return cleaned


class LocationForm(forms.Form):
    location_text = forms.CharField(label="Település vagy cím", max_length=200, required=False, widget=CITY_INPUT)
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned = super().clean()
        fill_coords(self, "location_text")
        return cleaned


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["message"]
        labels = {"message": "Rövid üzenet a hirdetőnek"}
        widgets = {"message": forms.Textarea(attrs={"rows": 3, "maxlength": 500})}

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) > 500:
            raise forms.ValidationError("Legfeljebb 500 karakter lehet.")
        return message


class ServiceListingForm(forms.ModelForm):
    class Meta:
        model = ServiceListing
        fields = ["title", "category", "description", "service_area", "price_category"]
        labels = {
            "title": "Megnevezés", "category": "Kategória", "description": "Leírás",
            "service_area": "Működési terület", "price_category": "Árkategória",
        }
        widgets = {"service_area": CITY_INPUT}

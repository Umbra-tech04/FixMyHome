from django.urls import path

from listings import views

app_name = "listings"

urlpatterns = [
    path("hirdetes/uj/", views.ad_create, name="ad_create"),
    path("hirdeteseim/", views.my_ads, name="my_ads"),
    path("hirdetes/<int:pk>/", views.ad_detail, name="ad_detail"),
    path("hirdetes/<int:pk>/szerkesztes/", views.ad_edit, name="ad_edit"),
    path("hirdetes/<int:pk>/allapot/", views.ad_set_status, name="ad_set_status"),
    path("hirdetes/<int:pk>/jelentkezes/", views.apply, name="apply"),
    path("hirdetes/<int:pk>/jelentkezes/visszavonas/", views.withdraw_application, name="withdraw_application"),
    path("hirdetes/<int:pk>/kivalasztas/<int:application_pk>/", views.choose_master, name="choose_master"),
    path("helyem/", views.save_location, name="save_location"),
    path("mesterek/", views.nearby_masters, name="nearby_masters"),
    path("api/mesterek/", views.api_masters, name="api_masters"),
    path("mester/profil/", views.master_profile, name="master_profile"),
    path("mester/hirdetesek/", views.master_ads, name="master_ads"),
    path("munkaim/", views.my_jobs, name="my_jobs"),
    path("szolgaltatasaim/", views.service_list, name="service_list"),
    path("szolgaltatasaim/uj/", views.service_form, name="service_create"),
    path("szolgaltatasaim/<int:pk>/szerkesztes/", views.service_form, name="service_edit"),
    path("szolgaltatasaim/<int:pk>/szuneteltetes/", views.service_toggle, name="service_toggle"),
    path("szolgaltatasaim/<int:pk>/torles/", views.service_delete, name="service_delete"),
]

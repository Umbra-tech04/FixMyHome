from django.urls import path

from accounts import views

urlpatterns = [
    path("regisztracio/", views.register, name="register"),
]

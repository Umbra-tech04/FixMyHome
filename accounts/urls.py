from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from accounts import views

urlpatterns = [
    path("regisztracio/", views.register, name="register"),
    path("belepes/", LoginView.as_view(), name="login"),
    path("kilepes/", LogoutView.as_view(), name="logout"),
]

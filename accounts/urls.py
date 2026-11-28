from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from accounts import views

urlpatterns = [
    path("regisztracio/", views.register, name="register"),
    path("regisztracio/elkuldve/", views.verification_sent, name="verification_sent"),
    # Belépve a LOGIN_REDIRECT_URL-re (főoldal) irányít. Nincs hurok: rossz szerepkörnél 403 jön, nem belépés.
    path("belepes/", LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("kilepes/", LogoutView.as_view(), name="logout"),
    path("email-megerosites/<str:token>/", views.verify_email, name="verify_email"),
]

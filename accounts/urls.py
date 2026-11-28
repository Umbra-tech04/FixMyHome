from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from accounts import views
from accounts.forms import EmailAuthenticationForm

urlpatterns = [
    path("regisztracio/", views.register, name="register"),
    path("regisztracio/elkuldve/", views.verification_sent, name="verification_sent"),
    # Belépve a LOGIN_REDIRECT_URL-re (főoldal) irányít. Nincs hurok: rossz szerepkörnél 403 jön, nem belépés.
    path(
        "belepes/",
        LoginView.as_view(redirect_authenticated_user=True, authentication_form=EmailAuthenticationForm),
        name="login",
    ),
    path("kilepes/", LogoutView.as_view(), name="logout"),
    # The fixed paths come before <token>, which would also match "ujrakuldes".
    path("email-megerosites/ujrakuldes/", views.resend_verification, name="resend_verification"),
    path("email-megerosites/ujrakuldes/elkuldve/", views.resend_verification_sent, name="resend_verification_sent"),
    path("email-megerosites/<str:token>/", views.verify_email, name="verify_email"),
]

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from listings import views as listings_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("listings.urls")),
    path("", listings_views.home, name="home"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

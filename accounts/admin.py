from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.forms import AdminEmailAuthenticationForm
from accounts.models import MasterProfile, User

# The /admin/ login refuses unverified accounts too (staff accounts are verified by default).
admin.site.login_form = AdminEmailAuthenticationForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Adatok", {"fields": ("name", "phone", "role")}),
        ("Jogosultságok", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dátumok", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "role", "password1", "password2")}),
    )


@admin.register(MasterProfile)
class MasterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profession", "service_area")
    search_fields = ("user__email", "user__name")

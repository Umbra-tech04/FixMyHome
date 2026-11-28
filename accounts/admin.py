from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.forms import AdminEmailAuthenticationForm
from accounts.models import MasterProfile, User, mark_email_verified

# The /admin/ login refuses unverified accounts too (staff accounts are verified by default).
admin.site.login_form = AdminEmailAuthenticationForm


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "email_verified", "is_staff")
    list_filter = ("role", "email_verified", "is_staff", "is_active")
    actions = ["mark_email_verified"]
    search_fields = ("email", "name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Adatok", {"fields": ("name", "phone", "role", "email_verified")}),
        ("Jogosultságok", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dátumok", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "role", "password1", "password2")}),
    )

    @admin.action(description="Kijelöltek e-mail-címének megerősítése")
    def mark_email_verified(self, request, queryset):
        changed = mark_email_verified(queryset.values_list("pk", flat=True))
        self.message_user(request, f"{changed} fiók e-mail-címe megerősítve.", messages.SUCCESS)


@admin.register(MasterProfile)
class MasterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profession", "service_area")
    search_fields = ("user__email", "user__name")

from django.contrib import admin

from listings.models import Ad, AdImage, Application, Category, ServiceListing


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "owner__email")


@admin.register(AdImage)
class AdImageAdmin(admin.ModelAdmin):
    list_display = ("ad", "image")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("ad", "master", "created_at")


@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ("title", "master", "category", "price_category", "is_active")
    list_filter = ("is_active", "category", "price_category")

from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField("név", max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "kategória"
        verbose_name_plural = "kategóriák"

    def __str__(self):
        return self.name


class Ad(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Nyitott"
        IN_PROGRESS = "in_progress", "Folyamatban"
        DONE = "done", "Lezárva"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ads")
    title = models.CharField("cím", max_length=150)
    description = models.TextField("leírás")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="kategória")
    location_text = models.CharField("helyszín", max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField("állapot", max_length=20, choices=Status.choices, default=Status.OPEN)
    chosen_master = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="chosen_ads",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "hirdetés"
        verbose_name_plural = "hirdetések"

    def __str__(self):
        return self.title


class AdImage(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ads/")


class Application(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="applications")
    master = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["ad", "master"], name="unique_application_per_ad_and_master")]
        verbose_name = "jelentkezés"
        verbose_name_plural = "jelentkezések"

    def __str__(self):
        return f"{self.master} → {self.ad}"


class ServiceListing(models.Model):
    class PriceCategory(models.TextChoices):
        LOW = "low", "Olcsó"
        MEDIUM = "medium", "Közepes"
        HIGH = "high", "Drága"

    master = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="services")
    title = models.CharField("megnevezés", max_length=150)
    description = models.TextField("leírás")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="kategória")
    service_area = models.CharField("működési terület", max_length=200)
    price_category = models.CharField("árkategória", max_length=10, choices=PriceCategory.choices)
    is_active = models.BooleanField("aktív", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "szolgáltatás-hirdetés"
        verbose_name_plural = "szolgáltatás-hirdetések"

    def __str__(self):
        return self.title

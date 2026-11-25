from django.conf import settings
from django.core.exceptions import ValidationError
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
        WITHDRAWN = "withdrawn", "Visszavonva"

    # Az összes állapotszabály itt van: csak előre lehet lépni, a lezárt/visszavont végállapot.
    TRANSITIONS = {
        Status.OPEN: {Status.IN_PROGRESS, Status.WITHDRAWN},
        Status.IN_PROGRESS: {Status.DONE},
    }
    BADGE_CLASSES = {
        Status.OPEN: "badge-open",
        Status.IN_PROGRESS: "badge-progress",
        Status.DONE: "badge-closed",
        Status.WITHDRAWN: "badge-withdrawn",
    }

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

    def can_transition_to(self, status):
        return status in self.TRANSITIONS.get(self.status, ())

    def transition_to(self, status):
        if not self.can_transition_to(status):
            target = dict(self.Status.choices).get(status, status)
            raise ValidationError(f"Ez az állapotváltás nem lehetséges: {self.get_status_display()} → {target}.")
        self.status = status

    def choose(self, master):
        self.transition_to(self.Status.IN_PROGRESS)
        self.chosen_master = master
        self.save(update_fields=["status", "chosen_master"])

    @property
    def accepts_applications(self):
        return self.status == self.Status.OPEN

    @property
    def is_editable(self):
        return self.status in (self.Status.OPEN, self.Status.IN_PROGRESS)

    @property
    def badge_class(self):
        return self.BADGE_CLASSES[self.status]


class AdImage(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ads/")


class Application(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="applications")
    master = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    message = models.TextField("üzenet", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["ad", "master"], name="unique_application_per_ad_and_master")]
        verbose_name = "jelentkezés"
        verbose_name_plural = "jelentkezések"

    def __str__(self):
        return f"{self.master} → {self.ad}"

    # Az állapot nincs tárolva: az ad.chosen_master-ből következik.
    STATUS_LABELS = {"pending": "Függőben", "accepted": "Elfogadva", "rejected": "Elutasítva"}
    STATUS_BADGES = {"pending": "badge-open", "accepted": "badge-progress", "rejected": "badge-withdrawn"}

    @property
    def status(self):
        chosen = self.ad.chosen_master_id
        if chosen is None:
            return "pending" if self.ad.status == Ad.Status.OPEN else "rejected"
        return "accepted" if chosen == self.master_id else "rejected"

    @property
    def status_label(self):
        return self.STATUS_LABELS[self.status]

    @property
    def badge_class(self):
        return self.STATUS_BADGES[self.status]


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

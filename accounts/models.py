from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    USER = "user", "Felhasználó"
    MASTER = "master", "Mester"
    SUPPORT = "support", "Ügyfélszolgálat"
    COMPANY = "company", "Cég"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Az e-mail-cím megadása kötelező.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class User(AbstractUser):
    username = None
    email = models.EmailField("e-mail", unique=True)
    name = models.CharField("név", max_length=150)
    phone = models.CharField("telefon", max_length=30, blank=True)
    role = models.CharField("szerepkör", max_length=20, choices=Role.choices, default=Role.USER)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def clean(self):
        super().clean()
        self.email = self.email.strip().lower()

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class MasterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="master_profile")
    profession = models.ForeignKey("listings.Category", on_delete=models.PROTECT, verbose_name="szakma")
    service_area = models.CharField("működési terület", max_length=200)
    contact = models.CharField("elérhetőség", max_length=200)
    latitude = models.FloatField("szélesség", null=True, blank=True)
    longitude = models.FloatField("hosszúság", null=True, blank=True)
    is_available = models.BooleanField("most elérhető", default=True)

    def __str__(self):
        return f"{self.user} ({self.profession})"

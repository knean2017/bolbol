from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

from .utils import format_phone_number, verify_phone_number



class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        """
        Create and return a user with an email, phone and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        if not phone:
            raise ValueError("The Phone field must be set")
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        """
        Create and return a superuser with an email, phone and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=14, unique=True)

    phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "first_name", "last_name"]

    objects = UserManager()


    def clean(self):
        super().clean()
        if self.phone:
            try:
                self.phone = format_phone_number(self.phone)
                verify_phone_number(self.phone)
            except ValueError as e:
                raise ValidationError({"phone": str(e)})

        if self.email:
            self.email = self.email.strip().lower()


class Store(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    category = models.ManyToManyField("products.category")
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    address_link = models.URLField(blank=True, null=True)


class StorePhone(models.Model):
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, related_name="phones")
    phone = models.CharField(max_length=14)

    def clean(self):
        super().clean()
        if self.phone:
            try:
                self.phone = format_phone_number(self.phone)
                verify_phone_number(self.phone)
            except ValueError as e:
                raise ValidationError({"phone": str(e)})
            

    class Meta:
        unique_together = ("store", "phone")


    def __str__(self):
        return self.phone
from django.db import models
from django.conf import Settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager



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
    USER_TYPES = [
        ("individual", "Individual User"),
        ("store", "Store/Business")
    ]

    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=14, unique=True)

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="individual")

    phone_verified = models.BooleanField(default=False)

    store_name = models.CharField(max_length=100, blank=True, null=True)
    store_description = models.TextField(blank=True, null=True)
    store_logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    store_address = models.TextField(blank=True, null=True)
    store_working_hours = models.CharField(max_length=200, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone"]

    objects = UserManager()

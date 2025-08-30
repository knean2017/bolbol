from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ..constants import *
from .category import SubCategory, Attribute
from .city import City
from django.db.models import F


class Product(models.Model):
    PROMOTION_LEVELS = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    )
    STATUS_LIST = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired")
    )

    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(SubCategory, null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[
            MinValueValidator(MIN_PRICE),
            MaxValueValidator(MAX_PRICE) 
        ]
    )
    views_count = models.PositiveIntegerField(default=0)

    promotion_level = models.CharField(
        max_length=10,
        choices=PROMOTION_LEVELS,
        default="basic"
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_LIST,
        null=True,
        blank=True,
        default="pending"
    )
    image = models.ImageField(upload_to="images/", blank=True, null=True)

    barter_available = models.BooleanField(default=False)
    credit_available = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.name
    
    def increment_view(self):
        self.views_count = F("views_count") + 1
        self.save(update_fields=["views_count"])
        self.refresh_from_db()


class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=50)
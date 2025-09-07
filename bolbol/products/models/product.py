from django.db import models
from django.db.models import F
from django.urls import reverse
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from ..constants import *
from .category import SubCategory, Attribute
from .city import City


class Product(models.Model):
    BASIC = "basic"
    PROMOTED = "promoted"
    SUPER_OPPORTUNITY = "super_opportunity"
    PREMIUM = "premium"
    VIP = "vip"

    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    EXPIRED = "expired"

    PROMOTION_LEVELS = (
        (BASIC, "Basic"),
        (PROMOTED, "Promoted"),
        (PREMIUM, "Premium"),
        (VIP, "VIP"),
    )

    STATUS_LIST = (
        (APPROVED, "Approved"),
        (PENDING, "Pending"),
        (REJECTED, "Rejected"),
        (EXPIRED, "Expired")
    )

    owner = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    store = models.ForeignKey("users.Store", on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=50)
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
        default=BASIC
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_LIST,
        null=True,
        blank=True,
        default=PENDING
    )
    image = models.ImageField(upload_to="images/", blank=True, null=True)

    is_product_new = models.BooleanField(default=False)
    is_mediator = models.BooleanField(default=False)
    is_barter_available = models.BooleanField(default=False)
    is_credit_available = models.BooleanField(default=False)
    is_delivery_available = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ["-updated_at"]


    def __str__(self):
        return self.title
    
    def increment_view(self):
        self.views_count = F("views_count") + 1
        self.save(update_fields=["views_count"])
        self.refresh_from_db()

    def get_absolute_url(self):
        path = reverse("product-detail", kwargs={"prod_id": self.id})
        return f"{settings.DOMAIN}{path}"


class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=50)

    
    def clean(self):
        data_type = self.attribute.data_type

        if data_type == self.attribute.INTEGER:
            try:
                int(self.value)
            except ValueError:
                raise ValidationError({"value": "Must be an integer."})
        
        elif data_type == self.attribute.FLOAT:
            try:
                float(self.value)
            except ValueError:
                raise ValidationError({"value": "Must be a float."})
            
        elif data_type == self.attribute.BOOLEAN:
            try:
                bool(self.value)
            except ValueError:
                raise ValidationError({"value": "Must be a boolean."})
        
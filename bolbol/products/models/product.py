from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ..constants import *
from products.models import SubCategory, City, Attribute


class Product(models.Model):
    PROMOTION_LEVELS = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    )

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

    promotion_level = models.CharField(
        max_length=10,
        choices=PROMOTION_LEVELS,
        default="basic"
    )

    image = models.ImageField(upload_to="images/", blank=True, null=True)

    barter_available = models.BooleanField(default=False)
    credit_available = models.BooleanField(default=False)
    delivery_available = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.name


class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=50)
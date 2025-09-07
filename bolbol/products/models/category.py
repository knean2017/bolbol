from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Subcategories"
        ordering = ["name"]


class Attribute(models.Model):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

    TYPES = [
        (STRING, "String"),
        (INTEGER, "Integer"),
        (FLOAT, "Float"),
        (BOOLEAN, "Boolean"),
    ]

    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=50)
    data_type = models.CharField(
        max_length=50,
        choices=TYPES,
        default=STRING
    )
    

    def __str__(self):
        return self.name
    
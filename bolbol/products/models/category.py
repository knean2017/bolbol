from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Subcategories"


class Attribute(models.Model):
    TYPES = [
        ("string", "String"),
        ("integer", "Integer"),
        ("float", "Float"),
        ("boolean", "Boolean"),
    ]
    subcategory = models.ForeignKey(SubCategory, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50)
    data_type = models.CharField(
        max_length=50,
        choices=TYPES
    )
    

    def __str__(self):
        return self.name
from django.db import models
from django.conf import settings


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} bookmarked {self.product}"
    

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} commented on {self.product}"
    
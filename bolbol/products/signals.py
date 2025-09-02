from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Product
from .tasks import send_email_notification


@receiver(post_save, sender=Product)
def send_create_email(sender, instance, created, **kwargs):
    if created:
        send_email_notification.delay(instance.id)

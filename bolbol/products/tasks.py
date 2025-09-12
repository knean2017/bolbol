from django.core.mail import send_mail
from celery import shared_task
from django.conf import settings
from .models import Product


#Not applied
@shared_task()
def send_email_notification(product_id):
    product = Product.objects.get(id=product_id)
    url = product.get_absolute_url()
    send_mail(
        "New Product Submitted",
        f"Thank you for submitting your product. You can view it here: {url}",
        settings.EMAIL_HOST_USER,
        ["knean6703@gmail.com"],
        fail_silently=False,
    )
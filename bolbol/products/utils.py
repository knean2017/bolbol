import secrets
from string import digits
from .constants import OTP_LENGTH
from django.core.cache import cache


def generate_otp(phone):
    otp = "".join(secrets.choice(digits) for _ in range(OTP_LENGTH))
    return otp


def verify_otp(phone, otp_entered):
    otp = cache.get(f"otp:{phone}")
    return otp == otp_entered


def mask_phone_number(phone):
    ...

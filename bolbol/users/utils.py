import secrets
from string import digits
from django.core.cache import cache

from .constants import OTP_LENGTH, PHONE_NUMBER_PREFIXES

def generate_otp(phone):
    otp = "".join(secrets.choice(digits) for _ in range(OTP_LENGTH))
    return otp


def verify_otp(phone, otp_entered):
    otp = cache.get(f"otp:{phone}")
    return otp == otp_entered


def verify_phone_number(phone: str):
    if len(phone) != 13:
        raise ValueError("Not a valid phone number.")
    
    prefix = phone[4:6]
    if prefix not in PHONE_NUMBER_PREFIXES:
        raise ValueError("Not a valid operator.")
    

def format_phone_number(phone: str):
    """
    Normalize phone numbers to +994XXXXXXXXX format.
    Removes spaces, dashes, or extra characters.
    """
    number = "".join(filter(str.isdigit, phone))

    if number.startswith("0"):
        number = "+994" + number[1:]
    
    if number.startswith("994"):
        number = "+" + number
    
    if len(number) == 9:
        number = "+994" + number

    return number    

def mask_phone_number(phone):
    ...

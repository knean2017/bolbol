import secrets
from string import digits
from django.core.cache import cache
import hashlib
import hmac

from .constants import OTP_LENGTH, PHONE_NUMBER_PREFIXES

def generate_otp(phone):
    otp = "".join(secrets.choice(digits) for _ in range(OTP_LENGTH))
    return otp


def cache_otp(phone, otp):
    otp_hash = hashlib.sha256(otp.encode()).hexdigest() # Hash the OTP before caching
    cache.set(f"otp:{phone}", otp_hash, timeout=300)  # 5 min expiry


def verify_otp(phone, otp_entered):
    otp_hash = cache.get(f"otp:{phone}")
    if not otp_hash:
        return False
    
    entered_hash = hashlib.sha256(otp_entered.encode()).hexdigest()
    return hmac.compare_digest(entered_hash, otp_hash) # Secure comparison


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


def verify_phone_number(phone: str):
    phone = format_phone_number(phone)

    if len(phone) != 13:
        raise ValueError("Not a valid phone number.")
    
    prefix = phone[4:6]
    if prefix not in PHONE_NUMBER_PREFIXES:
        raise ValueError("Not a valid operator.")
    

def mask_phone_number(phone):
    ...

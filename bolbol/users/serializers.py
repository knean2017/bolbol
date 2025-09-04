from rest_framework import serializers
from .models import User


class LoginRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=14, help_text="Phone number for OTP request")


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=14, help_text="Phone number")
    otp = serializers.CharField(max_length=6, help_text="OTP code received via SMS")


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_id = serializers.IntegerField()
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")


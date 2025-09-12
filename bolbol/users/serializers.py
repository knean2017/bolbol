from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

from .models import User
from .utils import format_phone_number, verify_phone_number


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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "first_name", "last_name", "phone_verified"]


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    phone = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )


    class Meta:
        model = User
        fields = ("email", "phone", "password", "first_name", "last_name")


    def validate_phone(self, value):
        """
        Normalize and validate phone number
        """

        formatted_phone = format_phone_number(value)

        try:
            verify_phone_number(formatted_phone)
        except ValueError as e:
            raise serializers.ValidationError(str(e))

        return formatted_phone 
    

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            phone=validated_data["phone"],
            password=validated_data["password"]
        )
        
        user.save()
        return user
    

# class RegisterStoreSerializer(serializers.ModelSerializer):
    
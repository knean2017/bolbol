from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema

from .models import User
from products.utils import generate_otp, verify_otp
from products.constants import OTP_TIMEOUT
from .serializers import LoginRequestSerializer, VerifyOTPSerializer, LoginResponseSerializer


class LoginAPIView(APIView):
    @swagger_auto_schema(request_body=LoginRequestSerializer)
    def post(self, request):
        phone = request.data.get("phone")

        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        otp = generate_otp(phone)
        cache.set(f"otp:{phone}", otp, timeout=OTP_TIMEOUT)

        print(f"{phone}: {otp}") # Test

        return Response({"message": "OTP sent succesfully"}, status=status.HTTP_200_OK)
    

class VerifyOTPCodeAPIView(APIView):
    @swagger_auto_schema(request_body=VerifyOTPSerializer, responses={200: LoginResponseSerializer})
    def post(self, request):
        phone = request.data.get("phone")
        otp = request.data.get("otp")

        if not phone or not otp:
            return Response({"error": "Phone number and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not verify_otp(phone, otp):
            return Response({f"error": "OTP is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        
        cache.delete(f"otp:{phone}")

        user = User.objects.filter(phone=phone).first()
        
        if not user.phone_verified:
            user.phone_verified = True
            user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "message": "Logged in succesfully",
            "user_id": user.pk,
            "access": access_token,
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)

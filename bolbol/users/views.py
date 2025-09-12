from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User
from .utils import generate_otp, cache_otp, verify_otp, format_phone_number
from .constants import OTP_TIMEOUT
from .serializers import LoginRequestSerializer, VerifyOTPSerializer, LoginResponseSerializer, UserSerializer, RegisterUserSerializer


class RegisterAPIView(APIView):
    @swagger_auto_schema(request_body=RegisterUserSerializer)
    def post(self, request):
        data = request.data
        serializer = RegisterUserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "Okay"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST   )


class LoginAPIView(APIView):
    @swagger_auto_schema(request_body=LoginRequestSerializer)
    def post(self, request):
        phone = format_phone_number(request.data.get("phone"))

        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not User.objects.filter(phone=phone).exists():
            return Response({"error": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        otp = generate_otp(phone)
        cache_otp(phone, otp)

        print(f"{phone}: {otp}") # Test

        return Response({"message": "OTP sent succesfully"}, status=status.HTTP_200_OK)
    

class VerifyOTPCodeAPIView(APIView):
    @swagger_auto_schema(request_body=VerifyOTPSerializer, responses={200: LoginResponseSerializer})
    def post(self, request):
        phone = format_phone_number(request.data.get("phone"))
        otp = request.data.get("otp")

        if not phone or not otp:
            return Response({"error": "Phone number and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not verify_otp(phone, otp):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        cache.delete(f"otp:{phone}")

        user = User.objects.filter(phone=phone).first()
        
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)  
        
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
    

class UserAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

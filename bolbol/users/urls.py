from django.urls import path

from .views import LoginAPIView, VerifyOTPCodeAPIView


urlpatterns = [
    path("login-otp/", LoginAPIView.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTPCodeAPIView.as_view(), name="login-otp")
]
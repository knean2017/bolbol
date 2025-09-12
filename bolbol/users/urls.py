from django.urls import path

from .views import LoginAPIView, VerifyOTPCodeAPIView, UserAPIView, RegisterAPIView


urlpatterns = [
    path("login-otp/", LoginAPIView.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTPCodeAPIView.as_view(), name="login-otp"),
    path("users/profile/", UserAPIView.as_view(), name="profile"),
    path("register/", RegisterAPIView.as_view(), name="register")
]